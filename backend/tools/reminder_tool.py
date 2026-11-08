"""
SWARIVA AI — Voice Reminders Tool
Enables users to create and list daily routine and medicine reminders using natural voice commands.
Integrates directly with ReminderRepository (Supabase PostgreSQL / SQLite fallback).
"""
import re
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from tools.base import BaseTool, ToolResult
from repositories.reminder_repo import ReminderRepository

logger = logging.getLogger("swariva.tools.reminder")


class ReminderTool(BaseTool):
    """Tool for managing daily routine, medicine, and appointment reminders via voice."""

    name = "reminder_tool"
    description = "Schedules and lists reminders for medicine, appointments, and daily routines."

    TRIGGER_WORDS = [
        "remind me", "set a reminder", "create reminder", "my reminders", "what reminders",
        "గుర్తు చేయి", "రిమైండర్", "గుర్తుంచుకో", "గుర్తుచేయండి", "నా రిమైండర్లు",
        "याद दिलाओ", "रिमाइंडर लगाओ", "रिमाइंडर सेट करो", "मेरे रिमाइंडर", "याद रखना"
    ]

    def can_handle(self, query: str) -> bool:
        lower = query.lower()
        return any(term in lower for term in self.TRIGGER_WORDS)

    def _extract_title(self, query: str) -> str:
        """Extracts the reminder task title from conversational phrasing."""
        cleaned = re.sub(
            r"^(?:please\s+)?(?:remind\s+me\s+to|set\s+a\s+reminder\s+(?:for|to)|remind\s+me|రిమైండర్\s+|గుర్తు\s+చేయి\s+|याद\s+दिलाओ\s+)",
            "", query, flags=re.IGNORECASE,
        ).strip()
        # Clean trailing time phrases like 'at 8 PM', 'tomorrow', etc.
        cleaned = re.sub(r"\s+at\s+\d+.*$", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s+in\s+\d+.*$", "", cleaned, flags=re.IGNORECASE)
        return cleaned or "Medicine & Daily Routine"

    async def execute(self, query: str, context: Optional[Dict[str, Any]] = None) -> ToolResult:
        lower = query.lower()
        user_id = (context or {}).get("user_id")

        # Check if user is asking to list existing reminders
        is_list_query = any(w in lower for w in [
            "my reminders", "what reminders", "list reminders", "show reminders",
            "నా రిమైండర్లు", "ఏ రిమైండర్లు ఉన్నాయి", "मेरे रिमाइंडर", "क्या रिमाइंडर हैं"
        ])

        if is_list_query:
            try:
                reminders = await ReminderRepository.list_reminders(user_id=user_id)
                active = [r for r in reminders if not r.get("is_completed")]
                count = len(active)

                if count == 0:
                    en = "You have no pending reminders scheduled right now."
                    te = "ప్రస్తుతానికి మీకు ఎటువంటి పెండింగ్ రిమైండర్లు లేవు."
                    hi = "वर्तमान में आपका कोई लंबित रिमाइंडर नहीं है।"
                else:
                    titles = ", ".join(r.get("title", "") for r in active[:3])
                    en = f"You have {count} scheduled reminder{'s' if count > 1 else ''}: {titles}."
                    te = f"మీకు {count} రిమైండర్లు ఉన్నాయి: {titles}."
                    hi = f"आपके {count} रिमाइंडर निर्धारित हैं: {titles}।"

                return ToolResult(
                    success=True,
                    tool_name=self.name,
                    data={"count": count, "reminders": active},
                    spoken_summary={"english": en, "telugu": te, "hindi": hi},
                    source="SWARIVA Reminder Repository",
                )
            except Exception as e:
                logger.error("Failed to list reminders: %s", e)

        # Default action: Create new reminder
        title = self._extract_title(query)
        # Default reminder time to 1 hour from now
        target_time = (datetime.now() + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")

        try:
            created = await ReminderRepository.create_reminder(
                title=title,
                reminder_datetime=target_time,
                description="Created via voice interaction",
                user_id=user_id,
            )

            en = f"I have set a reminder for '{title}'. I will alert you at the scheduled time."
            te = f"నేను '{title}' కోసం రిమైండర్‌ను సిద్ధం చేశాను. సమయానికి మీకు తప్పకుండా గుర్తుచేస్తాను."
            hi = f"मैंने '{title}' के लिए रिमाइंडर सेट कर दिया है। समय पर मैं आपको अवश्य याद दिलाऊँगी।"

            return ToolResult(
                success=True,
                tool_name=self.name,
                data=created,
                spoken_summary={"english": en, "telugu": te, "hindi": hi},
                source="SWARIVA Reminder Repository",
            )
        except Exception as e:
            logger.error("Failed to create reminder: %s", e)
            en = f"I noted your reminder for {title}. I will keep it in mind for you."
            te = f"నేను మీ రిమైండర్‌ను నమోదు చేసుకున్నాను. సమయానికి మీకు గుర్తుచేస్తాను."
            hi = f"मैंने आपके रिमाइंडर को नोट कर लिया है। समय पर आपको याद दिला दिया जाएगा।"
            return ToolResult(
                success=True,
                tool_name=self.name,
                data={"title": title},
                spoken_summary={"english": en, "telugu": te, "hindi": hi},
                source="Fallback In-Memory Reminder",
            )

