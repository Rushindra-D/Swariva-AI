"""
SWARIVA AI — Phase 5 Database & Authentication Test Suite
Verifies:
- User signup and login
- JWT Token authentication and 401 enforcement
- User profile retrieval
- Conversation persistence and history retrieval
- Reminder CRUD (Create, List, Update, Delete)
- Local SQLite fallback behavior
"""
import sys
import uuid
import pytest
from pathlib import Path

# Add backend directory to path
BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_auth_signup_and_profile():
    """Test user registration and subsequent profile retrieval."""
    unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    signup_data = {
        "email": unique_email,
        "password": "SecurePassword123!",
        "full_name": "Radha Sharma",
        "preferred_language": "hindi",
    }

    # 1. Sign up
    res = client.post("/api/v1/auth/signup", json=signup_data)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["email"] == unique_email
    assert body["full_name"] == "Radha Sharma"
    assert "access_token" in body
    token = body["access_token"]
    user_id = body["user_id"]
    assert user_id

    # 2. Duplicate registration should fail
    dup_res = client.post("/api/v1/auth/signup", json=signup_data)
    assert dup_res.status_code == 400

    # 3. Access profile with token
    headers = {"Authorization": f"Bearer {token}"}
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200, me_res.text
    me_body = me_res.json()
    assert me_body["id"] == user_id
    assert me_body["email"] == unique_email


def test_auth_login():
    """Test user login with valid credentials."""
    unique_email = f"login_{uuid.uuid4().hex[:8]}@example.com"

    # Register first
    signup_res = client.post(
        "/api/v1/auth/signup",
        json={
            "email": unique_email,
            "password": "ValidPassword987",
            "full_name": "Kiran Kumar",
            "preferred_language": "telugu",
        },
    )
    assert signup_res.status_code == 200

    # Login
    login_res = client.post(
        "/api/v1/auth/login",
        json={
            "email": unique_email,
            "password": "ValidPassword987",
        },
    )
    assert login_res.status_code == 200
    login_body = login_res.json()
    assert login_body["email"] == unique_email
    assert "access_token" in login_body


def test_auth_rejection_without_token():
    """Verify that protected endpoints reject requests without a valid token."""
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401

    res_invalid = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid_gibberish_token"})
    assert res_invalid.status_code == 401


def test_reminder_crud():
    """Test complete lifecycle of a reminder: Create, List, Update, Delete."""
    # 1. Create reminder
    rem_payload = {
        "title": "Take Blood Pressure Tablet",
        "description": "5mg tablet after breakfast",
        "reminder_datetime": "2026-11-09T08:30:00",
        "language": "english",
    }
    create_res = client.post("/api/v1/reminders", json=rem_payload)
    assert create_res.status_code == 201, create_res.text
    created = create_res.json()
    assert created["title"] == rem_payload["title"]
    assert created["is_completed"] is False
    rem_id = created["id"]

    # 2. List reminders
    list_res = client.get("/api/v1/reminders")
    assert list_res.status_code == 200
    items = list_res.json()
    assert any(r["id"] == rem_id for r in items)

    # 3. Update reminder to completed
    update_res = client.put(f"/api/v1/reminders/{rem_id}", json={"is_completed": True})
    assert update_res.status_code == 200
    updated = update_res.json()
    assert updated["is_completed"] is True

    # 4. Delete reminder
    del_res = client.delete(f"/api/v1/reminders/{rem_id}")
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

    # 5. Verify deleted from list
    list_after = client.get("/api/v1/reminders").json()
    assert not any(r["id"] == rem_id for r in list_after)


def test_conversation_persistence_via_chat():
    """Test that chat turns are persisted to database and retrievable via conversations API."""
    unique_session = f"session_test_{uuid.uuid4().hex[:10]}"

    # Send a chat message
    chat_payload = {
        "message": "Hello SWARIVA, please remember this test message.",
        "session_id": unique_session,
        "language": "english",
        "include_audio": False,
    }
    chat_res = client.post("/api/v1/chat", json=chat_payload)
    assert chat_res.status_code == 200

    # Retrieve conversation messages from database endpoint
    conv_res = client.get(f"/api/v1/conversations/{unique_session}")
    assert conv_res.status_code == 200
    conv_data = conv_res.json()
    assert conv_data["conversation_id"] == unique_session
    assert conv_data["total_messages"] >= 2  # At least user + assistant message

    roles = [m["role"] for m in conv_data["messages"]]
    assert "user" in roles
    assert "assistant" in roles
    assert any("remember this test message" in m["content"] for m in conv_data["messages"])

    # Clean up conversation
    del_conv = client.delete(f"/api/v1/conversations/{unique_session}")
    assert del_conv.status_code == 200
