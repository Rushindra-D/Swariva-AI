"""
SWARIVA AI — Conversation Repository
Persistent storage for multi-turn dialogues and message history.
Enforces strict user isolation and explicit cloud vs fallback execution.
"""
import uuid
import time
import json
import logging
from typing import List, Dict, Optional, Any

from database import (
    is_supabase_configured,
    get_supabase_admin_client,
    get_local_db,
)

logger = logging.getLogger("swariva.repo.conversation")


class ConversationRepository:
    """Manages persistent conversations and dialogue messages with tenant isolation."""

    @staticmethod
    def get_or_create_conversation(
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        title: str = "New Voice Conversation",
        language: str = "auto",
    ) -> Dict[str, Any]:
        """Fetches an existing conversation or inserts a new record."""
        cid = conversation_id or str(uuid.uuid4())
        now = time.strftime("%Y-%m-%d %H:%M:%S")

        # ── 1. Cloud Mode (Supabase PostgreSQL) ──
        if is_supabase_configured():
            client = get_supabase_admin_client()
            try:
                res = client.table("conversations").select("*").eq("id", cid).execute()
                if res.data and len(res.data) > 0:
                    return res.data[0]

                new_row = {
                    "id": cid,
                    "title": title,
                    "language": language,
                    "updated_at": "now()",
                }
                if user_id:
                    new_row["user_id"] = user_id

                ins = client.table("conversations").insert(new_row).execute()
                return ins.data[0] if ins.data else new_row
            except Exception as e:
                logger.error("Supabase get_or_create_conversation failed: %s", e)
                raise RuntimeError(f"Supabase get_or_create_conversation failed: {str(e)}")

        # ── 2. Local Fallback Mode (SQLite) ──
        conn = get_local_db()
        cursor = conn.cursor()
        row = cursor.execute("SELECT * FROM conversations WHERE id = ?", (cid,)).fetchone()
        if row:
            res = dict(row)
            conn.close()
            return res

        cursor.execute(
            "INSERT INTO conversations (id, user_id, title, language, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (cid, user_id, title, language, now, now),
        )
        conn.commit()
        conn.close()

        return {
            "id": cid,
            "user_id": user_id,
            "title": title,
            "language": language,
            "created_at": now,
            "updated_at": now,
        }

    @staticmethod
    def save_message(
        conversation_id: str,
        role: str,
        content: str,
        audio_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Appends a new message turn to the conversation."""
        mid = str(uuid.uuid4())
        meta = audio_metadata or {}
        now = time.strftime("%Y-%m-%d %H:%M:%S")

        # ── 1. Cloud Mode (Supabase PostgreSQL) ──
        if is_supabase_configured():
            client = get_supabase_admin_client()
            try:
                ConversationRepository.get_or_create_conversation(conversation_id)

                row = {
                    "id": mid,
                    "conversation_id": conversation_id,
                    "role": role,
                    "content": content,
                    "audio_metadata": meta,
                }
                res = client.table("messages").insert(row).execute()
                client.table("conversations").update({"updated_at": "now()"}).eq("id", conversation_id).execute()
                return res.data[0] if res.data else row
            except Exception as e:
                logger.error("Supabase save_message failed: %s", e)
                raise RuntimeError(f"Supabase save_message failed: {str(e)}")

        # ── 2. Local Fallback Mode (SQLite) ──
        conn = get_local_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO messages (id, conversation_id, role, content, audio_metadata, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (mid, conversation_id, role, content, json.dumps(meta), now),
        )
        cursor.execute("UPDATE conversations SET updated_at = ? WHERE id = ?", (now, conversation_id))
        conn.commit()
        conn.close()

        return {
            "id": mid,
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "audio_metadata": meta,
            "created_at": now,
        }

    @staticmethod
    def get_messages(conversation_id: str, user_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves messages for a conversation, verifying ownership if user_id is provided."""
        # ── 1. Cloud Mode (Supabase PostgreSQL) ──
        if is_supabase_configured():
            client = get_supabase_admin_client()
            try:
                # If user_id is given, check conversation ownership
                if user_id:
                    conv_check = client.table("conversations").select("user_id").eq("id", conversation_id).execute()
                    if conv_check.data:
                        owner = conv_check.data[0].get("user_id")
                        if owner and owner != user_id:
                            logger.warning("Unauthorized conversation access attempt: user %s on %s", user_id, conversation_id)
                            return []

                res = (
                    client.table("messages")
                    .select("*")
                    .eq("conversation_id", conversation_id)
                    .order("created_at", desc=False)
                    .limit(limit)
                    .execute()
                )
                return res.data or []
            except Exception as e:
                logger.error("Supabase get_messages failed: %s", e)
                raise RuntimeError(f"Supabase get_messages failed: {str(e)}")

        # ── 2. Local Fallback Mode (SQLite) ──
        conn = get_local_db()
        cursor = conn.cursor()

        if user_id:
            conv_row = cursor.execute("SELECT user_id FROM conversations WHERE id = ?", (conversation_id,)).fetchone()
            if conv_row and conv_row["user_id"] and conv_row["user_id"] != user_id:
                conn.close()
                return []

        rows = cursor.execute(
            "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC LIMIT ?",
            (conversation_id, limit),
        ).fetchall()

        result = []
        for r in rows:
            d = dict(r)
            try:
                d["audio_metadata"] = json.loads(d["audio_metadata"]) if d["audio_metadata"] else {}
            except Exception:
                d["audio_metadata"] = {}
            result.append(d)

        conn.close()
        return result

    @staticmethod
    def list_conversations(user_id: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Lists active conversations scoped strictly to user (or guest)."""
        # ── 1. Cloud Mode (Supabase PostgreSQL) ──
        if is_supabase_configured():
            client = get_supabase_admin_client()
            try:
                query = client.table("conversations").select("*").order("updated_at", desc=True).limit(limit)
                if user_id:
                    query = query.eq("user_id", user_id)
                else:
                    query = query.is_("user_id", "null")
                res = query.execute()
                return res.data or []
            except Exception as e:
                logger.error("Supabase list_conversations failed: %s", e)
                raise RuntimeError(f"Supabase list_conversations failed: {str(e)}")

        # ── 2. Local Fallback Mode (SQLite) ──
        conn = get_local_db()
        cursor = conn.cursor()
        if user_id:
            rows = cursor.execute(
                "SELECT * FROM conversations WHERE user_id = ? ORDER BY updated_at DESC LIMIT ?",
                (user_id, limit),
            ).fetchall()
        else:
            rows = cursor.execute(
                "SELECT * FROM conversations WHERE user_id IS NULL ORDER BY updated_at DESC LIMIT ?",
                (limit,),
            ).fetchall()

        result = [dict(r) for r in rows]
        conn.close()
        return result

    @staticmethod
    def delete_conversation(conversation_id: str, user_id: Optional[str] = None) -> bool:
        """Deletes a conversation and its messages while enforcing ownership."""
        # ── 1. Cloud Mode (Supabase PostgreSQL) ──
        if is_supabase_configured():
            client = get_supabase_admin_client()
            try:
                query = client.table("conversations").delete().eq("id", conversation_id)
                if user_id:
                    query = query.eq("user_id", user_id)
                else:
                    query = query.is_("user_id", "null")
                res = query.execute()
                return bool(res.data)
            except Exception as e:
                logger.error("Supabase delete_conversation failed: %s", e)
                raise RuntimeError(f"Supabase delete_conversation failed: {str(e)}")

        # ── 2. Local Fallback Mode (SQLite) ──
        conn = get_local_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
        if user_id:
            cursor.execute("DELETE FROM conversations WHERE id = ? AND user_id = ?", (conversation_id, user_id))
        else:
            cursor.execute("DELETE FROM conversations WHERE id = ? AND user_id IS NULL", (conversation_id,))
        conn.commit()
        conn.close()
        return True
