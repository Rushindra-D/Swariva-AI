"""
SWARIVA AI — Reminders Endpoints
Persistent database storage for daily routine, medicine, and appointment reminders.
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status, Depends

from schemas.reminder import (
    ReminderCreateRequest,
    ReminderUpdateRequest,
    ReminderResponse,
)
from repositories.reminder_repo import ReminderRepository
from auth import get_current_user

router = APIRouter(prefix="/api/v1/reminders", tags=["Daily Reminders"])


@router.get("", response_model=List[ReminderResponse], summary="List scheduled reminders")
async def list_user_reminders(current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """
    Fetches all active and completed reminders.
    If authenticated, returns reminders scoped to the user.
    """
    user_id = current_user["id"] if current_user else None
    items = await ReminderRepository.list_reminders(user_id=user_id)
    return [ReminderResponse(**it) for it in items]


@router.post("", response_model=ReminderResponse, status_code=status.HTTP_201_CREATED, summary="Create a new reminder")
async def create_user_reminder(
    req: ReminderCreateRequest,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user),
):
    """
    Creates and stores a scheduled medicine or routine reminder.
    """
    user_id = current_user["id"] if current_user else None
    created = await ReminderRepository.create_reminder(
        title=req.title,
        reminder_datetime=req.reminder_datetime,
        description=req.description,
        language=req.language or "auto",
        user_id=user_id,
    )
    return ReminderResponse(**created)


@router.put("/{reminder_id}", response_model=ReminderResponse, summary="Update reminder")
async def update_user_reminder(
    reminder_id: str,
    req: ReminderUpdateRequest,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user),
):
    """
    Updates completion status or properties of a reminder.
    """
    user_id = current_user["id"] if current_user else None
    updated = await ReminderRepository.update_reminder(
        reminder_id=reminder_id,
        user_id=user_id,
        is_completed=req.is_completed,
        title=req.title,
        description=req.description,
        reminder_datetime=req.reminder_datetime,
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reminder '{reminder_id}' not found.",
        )
    return ReminderResponse(**updated)


@router.delete("/{reminder_id}", summary="Delete reminder")
async def delete_user_reminder(
    reminder_id: str,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user),
):
    """
    Removes a reminder permanently.
    """
    user_id = current_user["id"] if current_user else None
    deleted = await ReminderRepository.delete_reminder(reminder_id=reminder_id, user_id=user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reminder '{reminder_id}' not found.",
        )
    return {"success": True, "message": "Reminder deleted successfully."}

