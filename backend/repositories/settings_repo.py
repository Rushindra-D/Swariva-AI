"""
SWARIVA AI — Settings & Trusted Contacts Repository
Stores user accessibility preferences, voice delivery choices, and trusted emergency contacts.
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

logger = logging.getLogger("swariva.repo.settings")


class SettingsRepository:
    """Manages user preferences and trusted emergency contacts."""

    @staticmethod
    async def get_settings(user_id: str) -> Dict[str, Any]:
        """Fetches settings for a user, returning defaults if not found."""
        defaults = {
            "user_id": user_id,
            "preferred_language": "auto",
            "preferred_voice": "Nalini",
            "autoplay_enabled": True,
            "font_size": "normal",
            "high_contrast_enabled": False,
        }

        if is_supabase_configured():
            client = get_supabase_admin_client()
            try:
                res = client.table("user_settings").select("*").eq("user_id", user_id).execute()
                if res.data and len(res.data) > 0:
                    return res.data[0]
            except Exception as e:
                logger.error("Supabase get_settings failed: %s", e)

        conn = get_local_db()
        cursor = conn.cursor()
        row = cursor.execute("SELECT * FROM user_settings WHERE user_id = ?", (user_id,)).fetchone()
        conn.close()

        if row:
            d = dict(row)
            d["autoplay_enabled"] = bool(d["autoplay_enabled"])
            d["high_contrast_enabled"] = bool(d["high_contrast_enabled"])
            return d

        return defaults

    @staticmethod
    async def update_settings(user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Upserts user preferences."""
        now = time.strftime("%Y-%m-%d %H:%M:%S")

        if is_supabase_configured():
            client = get_supabase_admin_client()
            try:
                row = {**updates, "user_id": user_id, "updated_at": "now()"}
                res = client.table("user_settings").upsert(row).execute()
                return res.data[0] if res.data else row
            except Exception as e:
                logger.error("Supabase update_settings failed: %s", e)

        conn = get_local_db()
        cursor = conn.cursor()
        current = await SettingsRepository.get_settings(user_id)
        current.update(updates)

        sid = current.get("id") or str(uuid.uuid4())
        cursor.execute(
            """INSERT INTO user_settings
               (id, user_id, preferred_language, preferred_voice, autoplay_enabled, font_size, high_contrast_enabled, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(user_id) DO UPDATE SET
               preferred_language=excluded.preferred_language,
               preferred_voice=excluded.preferred_voice,
               autoplay_enabled=excluded.autoplay_enabled,
               font_size=excluded.font_size,
               high_contrast_enabled=excluded.high_contrast_enabled,
               updated_at=excluded.updated_at""",
            (
                sid,
                user_id,
                current["preferred_language"],
                current["preferred_voice"],
                1 if current["autoplay_enabled"] else 0,
                current["font_size"],
                1 if current["high_contrast_enabled"] else 0,
                now,
                now,
            ),
        )
        conn.commit()
        conn.close()
        return current

    @staticmethod
    async def add_trusted_contact(
        user_id: str,
        contact_name: str,
        contact_phone: str,
        consent_confirmed: bool = False,
    ) -> Dict[str, Any]:
        """Registers a trusted caregiver / emergency contact."""
        cid = str(uuid.uuid4())
        now = time.strftime("%Y-%m-%d %H:%M:%S")

        if is_supabase_configured():
            client = get_supabase_admin_client()
            try:
                row = {
                    "id": cid,
                    "user_id": user_id,
                    "contact_name": contact_name,
                    "contact_phone": contact_phone,
                    "consent_confirmed": consent_confirmed,
                }
                res = client.table("trusted_contacts").insert(row).execute()
                return res.data[0] if res.data else row
            except Exception as e:
                logger.error("Supabase add_trusted_contact failed: %s", e)

        conn = get_local_db()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO trusted_contacts (id, user_id, contact_name, contact_phone, consent_confirmed, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (cid, user_id, contact_name, contact_phone, 1 if consent_confirmed else 0, now),
        )
        conn.commit()
        conn.close()

        return {
            "id": cid,
            "user_id": user_id,
            "contact_name": contact_name,
            "contact_phone": contact_phone,
            "consent_confirmed": consent_confirmed,
            "created_at": now,
        }

