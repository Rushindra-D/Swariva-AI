"""
SWARIVA AI — Live Supabase Cloud Verification & RLS Security Suite
Performs real integration tests directly against Supabase PostgreSQL:
1. Table existence & schema accessibility (all 6 tables)
2. Supabase Auth user lifecycle and PostgreSQL triggers (handle_new_user)
3. Live Cloud CRUD operations (profiles, conversations, messages, reminders, settings, trusted_contacts)
4. PostgreSQL Row-Level Security (RLS) & tenant isolation using real user JWTs
5. Clean teardown with zero leftover test records
"""
import sys
import uuid
import time
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from database import (
    is_supabase_configured,
    get_supabase_admin_client,
    get_supabase_user_client,
    create_client,
)
from config import SUPABASE_URL, SUPABASE_SECRET_KEY, SUPABASE_PUBLISHABLE_KEY


def run_full_cloud_verification():
    print("=" * 75)
    print("SWARIVA AI — LIVE SUPABASE CLOUD & RLS SECURITY VERIFICATION")
    print("=" * 75)

    # ── 1. ENVIRONMENT & CREDENTIAL HYGIENE ──────────────────────────────────
    if not is_supabase_configured():
        print("❌ STATUS: FAIL — Supabase credentials not configured in .env.")
        return False

    print(f"✅ Supabase Project Endpoint : {SUPABASE_URL}")
    print(f"✅ Service Key Configured    : {'YES (Loaded securely)' if SUPABASE_SECRET_KEY else 'NO'}")
    print(f"✅ Publishable Key Configured: {'YES (Loaded securely)' if SUPABASE_PUBLISHABLE_KEY else 'NO'}")

    admin_client = get_supabase_admin_client()
    if not admin_client:
        print("❌ STATUS: FAIL — Could not initialize official supabase-py admin client.")
        return False
    print("✅ supabase-py Admin Client  : INITIALIZED")

    # ── 2. VERIFY ALL 6 TABLES ──────────────────────────────────────────────
    required_tables = [
        "profiles",
        "conversations",
        "messages",
        "reminders",
        "trusted_contacts",
        "user_settings",
    ]

    print("\n📋 1. Checking Live PostgreSQL Schema Accessibility:")
    table_statuses = {}
    for tbl in required_tables:
        try:
            res = admin_client.table(tbl).select("*").limit(1).execute()
            print(f"  • public.{tbl:18}: ✅ PASS (Accessible via PostgREST)")
            table_statuses[tbl] = True
        except Exception as e:
            print(f"  • public.{tbl:18}: ❌ FAIL ({str(e)[:60]})")
            table_statuses[tbl] = False

    if not all(table_statuses.values()):
        print("\n❌ VERIFICATION FAILED: One or more tables are not accessible.")
        return False

    # ── 3. TEST USERS CREATION & DATABASE TRIGGER VERIFICATION ──────────────
    print("\n👥 2. Testing Supabase Auth & PostgreSQL Triggers (handle_new_user):")
    unique_suffix = uuid.uuid4().hex[:8]
    email_a = f"swariva_test_user_a_{unique_suffix}@example.com"
    email_b = f"swariva_test_user_b_{unique_suffix}@example.com"
    password = "SecureTestPassword123!"

    user_a = None
    user_b = None

    try:
        # Create User A
        uA_res = admin_client.auth.admin.create_user({
            "email": email_a,
            "password": password,
            "email_confirm": True,
            "user_metadata": {
                "full_name": "Test User Alpha",
                "preferred_language": "telugu",
            },
        })
        user_a = uA_res.user
        uid_a = str(user_a.id)
        print(f"  • Created User A in auth.users (ID: {uid_a})")

        # Create User B
        uB_res = admin_client.auth.admin.create_user({
            "email": email_b,
            "password": password,
            "email_confirm": True,
            "user_metadata": {
                "full_name": "Test User Beta",
                "preferred_language": "hindi",
            },
        })
        user_b = uB_res.user
        uid_b = str(user_b.id)
        print(f"  • Created User B in auth.users (ID: {uid_b})")

        # Verify Trigger on_auth_user_created for User A
        time.sleep(0.5)  # Allow trigger execution
        prof_a = admin_client.table("profiles").select("*").eq("id", uid_a).execute()
        assert len(prof_a.data) == 1, "Profile not created by trigger"
        assert prof_a.data[0]["full_name"] == "Test User Alpha"
        assert prof_a.data[0]["preferred_language"] == "telugu"
        print("  • Trigger 'on_auth_user_created' -> public.profiles: ✅ PASS")

        settings_a = admin_client.table("user_settings").select("*").eq("user_id", uid_a).execute()
        assert len(settings_a.data) == 1, "User settings not created by trigger"
        print("  • Trigger 'on_auth_user_created' -> public.user_settings: ✅ PASS")

        # ── 4. LIVE CRUD OPERATIONS FOR USER A ──────────────────────────────
        print("\n🛠️ 3. Testing Cloud CRUD Operations (User A):")

        # Profiles Update
        admin_client.table("profiles").update({"full_name": "Alpha Verified"}).eq("id", uid_a).execute()
        prof_check = admin_client.table("profiles").select("full_name").eq("id", uid_a).execute()
        assert prof_check.data[0]["full_name"] == "Alpha Verified"
        print("  • Profile Update & Retrieval             : ✅ PASS")

        # User Settings Update
        admin_client.table("user_settings").update({
            "preferred_voice": "Kaveri",
            "font_size": "large",
            "high_contrast_enabled": True,
        }).eq("user_id", uid_a).execute()
        sett_check = admin_client.table("user_settings").select("*").eq("user_id", uid_a).execute()
        assert sett_check.data[0]["preferred_voice"] == "Kaveri"
        assert sett_check.data[0]["font_size"] == "large"
        assert sett_check.data[0]["high_contrast_enabled"] is True
        print("  • User Accessibility Settings Persistence: ✅ PASS")

        # Conversations
        conv_id = str(uuid.uuid4())
        admin_client.table("conversations").insert({
            "id": conv_id,
            "user_id": uid_a,
            "title": "Morning Routine Conversation",
            "language": "telugu",
        }).execute()
        conv_check = admin_client.table("conversations").select("*").eq("id", conv_id).execute()
        assert len(conv_check.data) == 1
        print("  • Conversation Creation & Retrieval       : ✅ PASS")

        # Messages (Multi-turn dialogue persistence)
        msg_user_id = str(uuid.uuid4())
        msg_asst_id = str(uuid.uuid4())
        admin_client.table("messages").insert([
            {
                "id": msg_user_id,
                "conversation_id": conv_id,
                "role": "user",
                "content": "నా బీపీ మందు ఎప్పుడు వేసుకోవాలి?",  # When should I take my BP medicine?
                "audio_metadata": {"stt_model": "prisma-v3.0", "confidence": 0.98},
            },
            {
                "id": msg_asst_id,
                "conversation_id": conv_id,
                "role": "assistant",
                "content": "ఉదయం అల్పాహారం తర్వాత ఒక మాత్ర తీసుకోండి.",  # Take 1 tablet after breakfast.
                "audio_metadata": {"tts_model": "timbre-v2.5", "voice": "Nalini"},
            },
        ]).execute()

        msgs_check = admin_client.table("messages").select("*").eq("conversation_id", conv_id).order("created_at").execute()
        assert len(msgs_check.data) == 2
        assert msgs_check.data[0]["role"] == "user"
        assert msgs_check.data[1]["role"] == "assistant"
        print("  • Multi-Turn Message Persistence (STT/TTS): ✅ PASS")

        # Reminders CRUD
        rem_id = str(uuid.uuid4())
        admin_client.table("reminders").insert({
            "id": rem_id,
            "user_id": uid_a,
            "title": "Blood Pressure Tablet (5mg)",
            "description": "Take 1 tablet with warm water",
            "reminder_datetime": "2026-11-10T08:30:00+00:00",
            "language": "telugu",
            "is_completed": False,
        }).execute()

        # Update reminder
        admin_client.table("reminders").update({"is_completed": True}).eq("id", rem_id).execute()
        rem_check = admin_client.table("reminders").select("*").eq("id", rem_id).execute()
        assert rem_check.data[0]["is_completed"] is True
        print("  • Reminder Creation & Update              : ✅ PASS")

        # Trusted Contacts
        tc_id = str(uuid.uuid4())
        admin_client.table("trusted_contacts").insert({
            "id": tc_id,
            "user_id": uid_a,
            "contact_name": "Dr. Ramesh (Cardiologist)",
            "contact_phone": "+919876543210",
            "consent_confirmed": True,
        }).execute()
        tc_check = admin_client.table("trusted_contacts").select("*").eq("id", tc_id).execute()
        assert len(tc_check.data) == 1
        print("  • Trusted Contact Registration            : ✅ PASS")

        # ── 5. AUTHENTICATED USER JWT & RLS TENANT ISOLATION ────────────────
        print("\n🛡️ 4. Testing PostgreSQL Row-Level Security (RLS) with Authenticated User JWTs:")

        # Obtain real authenticated JWT session tokens for User A and User B using isolated auth clients
        # (Avoid mutating admin_client session state)
        auth_anon_key = SUPABASE_PUBLISHABLE_KEY if SUPABASE_PUBLISHABLE_KEY else SUPABASE_SECRET_KEY
        auth_client_a = create_client(SUPABASE_URL, auth_anon_key)
        session_a = auth_client_a.auth.sign_in_with_password({"email": email_a, "password": password})
        token_a = session_a.session.access_token

        auth_client_b = create_client(SUPABASE_URL, auth_anon_key)
        session_b = auth_client_b.auth.sign_in_with_password({"email": email_b, "password": password})
        token_b = session_b.session.access_token

        # User A client (carries User A JWT)
        user_a_client = get_supabase_user_client(token_a)
        assert user_a_client is not None, "Failed to create User A client"

        # User B client (carries User B JWT)
        user_b_client = get_supabase_user_client(token_b)
        assert user_b_client is not None, "Failed to create User B client"

        # RLS Positive Verification: User A can read their own data
        a_query_rem = user_a_client.table("reminders").select("*").eq("id", rem_id).execute()
        assert len(a_query_rem.data) == 1, "RLS FAILURE: User A was unable to view own reminder!"
        print("  • RLS Positive Access: User A can view own reminder          : ✅ PASS (1 row returned)")

        # RLS TEST 1: User B queries public.profiles for User A
        b_query_prof = user_b_client.table("profiles").select("*").eq("id", uid_a).execute()
        assert len(b_query_prof.data) == 0, "RLS FAILURE: User B was able to view User A profile!"
        print("  • RLS Profiles Isolation: User B cannot view User A profile  : ✅ PASS (0 rows returned)")

        # RLS TEST 2: User B queries public.conversations for User A
        b_query_conv = user_b_client.table("conversations").select("*").eq("id", conv_id).execute()
        assert len(b_query_conv.data) == 0, "RLS FAILURE: User B was able to view User A conversation!"
        print("  • RLS Conversation Isolation: User B cannot view User A chat : ✅ PASS (0 rows returned)")

        # RLS TEST 3: User B queries public.messages for User A's conversation
        b_query_msgs = user_b_client.table("messages").select("*").eq("conversation_id", conv_id).execute()
        assert len(b_query_msgs.data) == 0, "RLS FAILURE: User B was able to view User A messages!"
        print("  • RLS Message Isolation: User B cannot view User A messages  : ✅ PASS (0 rows returned)")

        # RLS TEST 4: User B queries public.reminders for User A's reminder
        b_query_rem = user_b_client.table("reminders").select("*").eq("id", rem_id).execute()
        assert len(b_query_rem.data) == 0, "RLS FAILURE: User B was able to view User A reminder!"
        print("  • RLS Reminder Isolation: User B cannot view User A reminder : ✅ PASS (0 rows returned)")

        # RLS TEST 5: User B attempts to delete User A's reminder
        b_del_rem = user_b_client.table("reminders").delete().eq("id", rem_id).execute()
        assert len(b_del_rem.data) == 0, "RLS FAILURE: User B deleted User A reminder!"
        # Verify reminder still exists for User A
        rem_still_there = admin_client.table("reminders").select("*").eq("id", rem_id).execute()
        assert len(rem_still_there.data) == 1, "Reminder was unexpectedly deleted"
        print("  • RLS Reminder Write Protection: User B cannot delete User A: ✅ PASS (Blocked by RLS)")

        # RLS TEST 6: User B queries public.trusted_contacts for User A
        b_query_tc = user_b_client.table("trusted_contacts").select("*").eq("id", tc_id).execute()
        assert len(b_query_tc.data) == 0, "RLS FAILURE: User B was able to view User A contact!"
        print("  • RLS Trusted Contacts Isolation: User B cannot view contacts: ✅ PASS (0 rows returned)")

        # RLS TEST 7: User B queries public.user_settings for User A
        b_query_sett = user_b_client.table("user_settings").select("*").eq("user_id", uid_a).execute()
        assert len(b_query_sett.data) == 0, "RLS FAILURE: User B was able to view User A settings!"
        print("  • RLS Settings Isolation: User B cannot view User A settings : ✅ PASS (0 rows returned)")

        # ── 6. CLEANUP TEST ARTIFACTS ───────────────────────────────────────
        print("\n🧹 5. Teardown & Cascading Cleanup:")
        # Deleting users from auth.users triggers ON DELETE CASCADE across all 6 tables!
        admin_client.auth.admin.delete_user(uid_a)
        admin_client.auth.admin.delete_user(uid_b)
        print("  • Deleted User A and User B from auth.users")

        # Verify cascade
        check_rem_gone = admin_client.table("reminders").select("*").eq("id", rem_id).execute()
        assert len(check_rem_gone.data) == 0, "Reminder was not cascade-deleted"
        check_conv_gone = admin_client.table("conversations").select("*").eq("id", conv_id).execute()
        assert len(check_conv_gone.data) == 0, "Conversation was not cascade-deleted"
        check_prof_gone = admin_client.table("profiles").select("*").eq("id", uid_a).execute()
        assert len(check_prof_gone.data) == 0, "Profile was not cascade-deleted"
        print("  • Verified PostgreSQL ON DELETE CASCADE: ✅ PASS (Zero leftover audit records)")

        print("\n" + "=" * 75)
        print("🎉 LIVE SUPABASE CLOUD & RLS VERIFICATION: 100% PASS")
        print("=" * 75)
        return True

    except Exception as e:
        print(f"\n❌ CLOUD AUDIT FAILED: {e}")
        # Clean up any created users in finally/exception
        if user_a:
            try: admin_client.auth.admin.delete_user(str(user_a.id))
            except: pass
        if user_b:
            try: admin_client.auth.admin.delete_user(str(user_b.id))
            except: pass
        return False


if __name__ == "__main__":
    success = run_full_cloud_verification()
    sys.exit(0 if success else 1)
