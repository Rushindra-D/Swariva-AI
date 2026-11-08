"""
SWARIVA AI — Reminder Schemas
"""
from typing import Optional
from pydantic import BaseModel, Field


class ReminderCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    reminder_datetime: str = Field(..., description="ISO 8601 or HH:MM scheduled time string")
    description: Optional[str] = Field(None, max_length=1000)
    language: Optional[str] = Field("auto", description="Announcement language")


class ReminderUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    reminder_datetime: Optional[str] = None
    is_completed: Optional[bool] = None


class ReminderResponse(BaseModel):
    id: str
    user_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    reminder_datetime: str
    language: str = "auto"
    is_completed: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

