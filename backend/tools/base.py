"""
SWARIVA AI — Base Tool Interface
Defines the structure for tools and real-time RAG data fetchers.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class ToolResult:
    """Standardized response from a SWARIVA tool execution."""
    success: bool
    tool_name: str
    data: Dict[str, Any]
    spoken_summary: Dict[str, str]  # Multilingual spoken summary: {"english": "...", "telugu": "...", "hindi": "..."}
    source: str
    error: Optional[str] = None

    def get_spoken_text(self, language: str = "english") -> str:
        """Returns the spoken text for the requested language."""
        lang = language.lower()
        if "te" in lang:
            return self.spoken_summary.get("telugu") or self.spoken_summary.get("english", "")
        elif "hi" in lang:
            return self.spoken_summary.get("hindi") or self.spoken_summary.get("english", "")
        return self.spoken_summary.get("english", "")


class BaseTool(ABC):
    """Abstract base class for all tools in SWARIVA AI."""

    name: str = "base_tool"
    description: str = ""

    @abstractmethod
    def can_handle(self, query: str) -> bool:
        """Determines if this tool should handle the user query."""
        pass

    @abstractmethod
    async def execute(self, query: str, context: Optional[Dict[str, Any]] = None) -> ToolResult:
        """Executes the tool and returns structured result with spoken summaries."""
        pass
