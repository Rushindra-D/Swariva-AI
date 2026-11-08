"""
SWARIVA AI — Authentication Repository
Handles Supabase Auth user management, token verification, and profile synchronization.
"""
import uuid
import time
import logging
from typing import Optional, Dict, Any

from database import (
    is_supabase_configured,
    get_supabase_admin_client,
    get_local_db,
)

logger = logging.getLogger("swariva.repo.auth")


class AuthRepository:
    """Manages User Sign-Up, Sign-In, Token verification, and Profile sync."""

    @staticmethod
    async def sign_up(
        email: str,
        password: str,
        full_name: str = "Swariva User",
        preferred_language: str = "auto",
    ) -> Dict[str, Any]:
        """Registers a new user in Supabase Auth and triggers profile creation."""
        if is_supabase_configured():
            client = get_supabase_admin_client()
            try:
                auth_res = client.auth.sign_up({
                    "email": email,
                    "password": password,
                    "options": {
                        "data": {
                            "full_name": full_name,
                            "preferred_language": preferred_language,
                        }
                    }
                })

                user_id = str(auth_res.user.id) if auth_res.user else str(uuid.uuid4())
                access_token = auth_res.session.access_token if auth_res.session else "dev_token_" + user_id

                # Upsert profile record
                client.table("profiles").upsert({
                    "id": user_id,
                    "full_name": full_name,
                    "email": email,
                    "preferred_language": preferred_language,
                    "updated_at": "now()",
                }).execute()

                return {
                    "user_id": user_id,
                    "email": email,
                    "full_name": full_name,
                    "preferred_language": preferred_language,
                    "access_token": access_token,
                }
            except Exception as e:
                logger.error("Supabase signUp failed: %s", e)
                raise ValueError(f"Registration failed: {str(e)}")

        # ── Local SQLite Fallback ──
        user_id = "user_" + str(uuid.uuid4())[:12]
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        conn = get_local_db()
        cursor = conn.cursor()

        # Check existing email
        existing = cursor.execute("SELECT id FROM profiles WHERE email = ?", (email,)).fetchone()
        if existing:
            conn.close()
            raise ValueError("An account with this email already exists.")

        cursor.execute(
            "INSERT INTO profiles (id, full_name, email, preferred_language, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, full_name, email, preferred_language, now, now),
        )
        conn.commit()
        conn.close()

        return {
            "user_id": user_id,
            "email": email,
            "full_name": full_name,
            "preferred_language": preferred_language,
            "access_token": f"local_jwt_{user_id}_{int(time.time())}",
        }

    @staticmethod
    async def sign_in(email: str, password: str) -> Dict[str, Any]:
        """Authenticates user credentials and returns an access session."""
        if is_supabase_configured():
            client = get_supabase_admin_client()
            try:
                auth_res = client.auth.sign_in_with_password({
                    "email": email,
                    "password": password,
                })
                user_id = str(auth_res.user.id)
                access_token = auth_res.session.access_token

                # Fetch profile details
                profile_res = client.table("profiles").select("*").eq("id", user_id).single().execute()
                profile_data = profile_res.data or {}

                return {
                    "user_id": user_id,
                    "email": email,
                    "full_name": profile_data.get("full_name", "Swariva User"),
                    "preferred_language": profile_data.get("preferred_language", "auto"),
                    "access_token": access_token,
                }
            except Exception as e:
                logger.error("Supabase signIn failed: %s", e)
                raise ValueError(f"Invalid email or password: {str(e)}")

        # ── Local SQLite Fallback ──
        conn = get_local_db()
        cursor = conn.cursor()
        row = cursor.execute("SELECT * FROM profiles WHERE email = ?", (email,)).fetchone()

        if not row:
            # Auto-register for smooth local development
            user_id = "user_" + str(uuid.uuid4())[:12]
            now = time.strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(
                "INSERT INTO profiles (id, full_name, email, preferred_language, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, email.split("@")[0].title(), email, "auto", now, now),
            )
            conn.commit()
            row = cursor.execute("SELECT * FROM profiles WHERE id = ?", (user_id,)).fetchone()

        user_dict = dict(row)
        conn.close()

        return {
            "user_id": user_dict["id"],
            "email": user_dict["email"],
            "full_name": user_dict["full_name"],
            "preferred_language": user_dict["preferred_language"],
            "access_token": f"local_jwt_{user_dict['id']}_{int(time.time())}",
        }

    @staticmethod
    async def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """Verifies an incoming Bearer JWT token and returns user claims."""
        if not token:
            return None

        # Clean "Bearer " prefix if included
        token = token.replace("Bearer ", "").strip()

        if is_supabase_configured():
            client = get_supabase_admin_client()
            try:
                user_resp = client.auth.get_user(token)
                if user_resp and user_resp.user:
                    u = user_resp.user
                    return {
                        "id": str(u.id),
                        "email": u.email,
                        "user_metadata": u.user_metadata or {},
                    }
            except Exception as e:
                logger.warning("Token verification failed with Supabase: %s", e)

        # Local fallback token parser
        if token.startswith("local_jwt_"):
            body = token[len("local_jwt_"):]
            user_id = body.rsplit("_", 1)[0] if "_" in body else body
            return {
                "id": user_id,
                "email": f"{user_id}@swariva.ai",
                "user_metadata": {"full_name": "Authenticated User"},
            }
        elif token.startswith("dev_token_"):
            user_id = token[len("dev_token_"):]
            return {
                "id": user_id,
                "email": f"{user_id}@swariva.ai",
                "user_metadata": {"full_name": "Authenticated User"},
            }

        return None

    @staticmethod
    async def get_profile(user_id: str) -> Optional[Dict[str, Any]]:
        """Fetch profile for a user ID."""
        if is_supabase_configured():
            client = get_supabase_admin_client()
            try:
                res = client.table("profiles").select("*").eq("id", user_id).single().execute()
                return res.data
            except Exception as e:
                logger.error("Error fetching Supabase profile: %s", e)

        conn = get_local_db()
        cursor = conn.cursor()
        row = cursor.execute("SELECT * FROM profiles WHERE id = ?", (user_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

