"""
SWARIVA AI — Reminder Repository
Persistent database storage for daily routine, medicine, and appointment reminders.
Enforces strict user isolation and explicit cloud vs fallback execution.
"""
import uuid
import time
import logging
from typing import List, Dict, Optional, Any

from database import (
    is_supabase_configured,
    get_supabase_admin_client,
    get_local_db,
)

logger = logging.getLogger("swariva.repo.reminder")


class ReminderRepository:
    """Manages persistent medicine and schedule reminders with tenant isolation."""

    @staticmethod
    async def create_reminder(
        title: str,
        reminder_datetime: str,
        description: Optional[str] = None,
        language: str = "auto",
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Creates and stores a scheduled reminder."""
        rid = str(uuid.uuid4())
        now = time.strftime("%Y-%m-%d %H:%M:%S")

        # ── 1. Cloud Mode (Supabase PostgreSQL) ──
        if is_supabase_configured():
            client = get_supabase_admin_client()
            try:
                row = {
                    "id": rid,
                    "title": title,
                    "description": description or "",
                    "reminder_datetime": reminder_datetime,
                    "language": language,
                    "is_completed": False,
                }
                if user_id:
                    row["user_id"] = user_id

                res = client.table("reminders").insert(row).execute()
                return res.data[0] if res.data else row
            except Exception as e:
                logger.error("Supabase create_reminder failed: %s", e)
                raise RuntimeError(f"Supabase create_reminder failed: {str(e)}")

        # ── 2. Local Fallback Mode (SQLite) ──
        conn = get_local_db()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO reminders
               (id, user_id, title, description, reminder_datetime, language, is_completed, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?)""",
            (rid, user_id, title, description or "", reminder_datetime, language, now, now),
        )
        conn.commit()
        conn.close()

        return {
            "id": rid,
            "user_id": user_id,
            "title": title,
            "description": description or "",
            "reminder_datetime": reminder_datetime,
            "language": language,
            "is_completed": False,
            "created_at": now,
            "updated_at": now,
        }

    @staticmethod
    async def list_reminders(user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lists reminders strictly scoped to the user (or guest)."""
        # ── 1. Cloud Mode (Supabase PostgreSQL) ──
        if is_supabase_configured():
            client = get_supabase_admin_client()
            try:
                query = client.table("reminders").select("*").order("reminder_datetime", desc=False)
                if user_id:
                    query = query.eq("user_id", user_id)
                else:
                    query = query.is_("user_id", "null")
                res = query.execute()
                return res.data or []
            except Exception as e:
                logger.error("Supabase list_reminders failed: %s", e)
                raise RuntimeError(f"Supabase list_reminders failed: {str(e)}")

        # ── 2. Local Fallback Mode (SQLite) ──
        conn = get_local_db()
        cursor = conn.cursor()
        if user_id:
            rows = cursor.execute(
                "SELECT * FROM reminders WHERE user_id = ? ORDER BY reminder_datetime ASC",
                (user_id,),
            ).fetchall()
        else:
            rows = cursor.execute(
                "SELECT * FROM reminders WHERE user_id IS NULL ORDER BY reminder_datetime ASC"
            ).fetchall()

        result = []
        for r in rows:
            d = dict(r)
            d["is_completed"] = bool(d["is_completed"])
            result.append(d)
        conn.close()
        return result

    @staticmethod
    async def update_reminder(
        reminder_id: str,
        user_id: Optional[str] = None,
        is_completed: Optional[bool] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        reminder_datetime: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Updates reminder status or properties while enforcing ownership."""
        now = time.strftime("%Y-%m-%d %H:%M:%S")

        # ── 1. Cloud Mode (Supabase PostgreSQL) ──
        if is_supabase_configured():
            client = get_supabase_admin_client()
            try:
                updates = {"updated_at": "now()"}
                if is_completed is not None:
                    updates["is_completed"] = is_completed
                if title is not None:
                    updates["title"] = title
                if description is not None:
                    updates["description"] = description
                if reminder_datetime is not None:
                    updates["reminder_datetime"] = reminder_datetime

                query = client.table("reminders").update(updates).eq("id", reminder_id)
                if user_id:
                    query = query.eq("user_id", user_id)
                else:
                    query = query.is_("user_id", "null")

                res = query.execute()
                return res.data[0] if res.data else None
            except Exception as e:
                logger.error("Supabase update_reminder failed: %s", e)
                raise RuntimeError(f"Supabase update_reminder failed: {str(e)}")

        # ── 2. Local Fallback Mode (SQLite) ──
        conn = get_local_db()
        cursor = conn.cursor()

        set_clauses = ["updated_at = ?"]
        params = [now]
        if is_completed is not None:
            set_clauses.append("is_completed = ?")
            params.append(1 if is_completed else 0)
        if title is not None:
            set_clauses.append("title = ?")
            params.append(title)
        if description is not None:
            set_clauses.append("description = ?")
            params.append(description)
        if reminder_datetime is not None:
            set_clauses.append("reminder_datetime = ?")
            params.append(reminder_datetime)

        params.append(reminder_id)
        where_clause = "WHERE id = ?"
        if user_id:
            where_clause += " AND user_id = ?"
            params.append(user_id)
        else:
            where_clause += " AND user_id IS NULL"

        query = f"UPDATE reminders SET {', '.join(set_clauses)} {where_clause}"
        cursor.execute(query, tuple(params))
        if cursor.rowcount == 0:
            conn.close()
            return None

        conn.commit()
        row = cursor.execute("SELECT * FROM reminders WHERE id = ?", (reminder_id,)).fetchone()
        conn.close()

        if row:
            d = dict(row)
            d["is_completed"] = bool(d["is_completed"])
            return d
        return None

    @staticmethod
    async def delete_reminder(reminder_id: str, user_id: Optional[str] = None) -> bool:
        """Deletes a reminder record with ownership verification."""
        # ── 1. Cloud Mode (Supabase PostgreSQL) ──
        if is_supabase_configured():
            client = get_supabase_admin_client()
            try:
                query = client.table("reminders").delete().eq("id", reminder_id)
                if user_id:
                    query = query.eq("user_id", user_id)
                else:
                    query = query.is_("user_id", "null")

                res = query.execute()
                return bool(res.data)
            except Exception as e:
                logger.error("Supabase delete_reminder failed: %s", e)
                raise RuntimeError(f"Supabase delete_reminder failed: {str(e)}")

        # ── 2. Local Fallback Mode (SQLite) ──
        conn = get_local_db()
        cursor = conn.cursor()
        if user_id:
            cursor.execute("DELETE FROM reminders WHERE id = ? AND user_id = ?", (reminder_id, user_id))
        else:
            cursor.execute("DELETE FROM reminders WHERE id = ? AND user_id IS NULL", (reminder_id,))
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        return deleted_count > 0
