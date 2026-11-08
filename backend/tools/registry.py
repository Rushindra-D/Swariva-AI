"""
SWARIVA AI — Tool Registry and Execution Dispatcher
Coordinates tool selection, execution, and RAG context compilation.
"""
import logging
from typing import List, Dict, Any, Optional

from tools.base import BaseTool, ToolResult
from tools.weather_tool import WeatherTool
from tools.gold_price_tool import GoldPriceTool
from tools.reminder_tool import ReminderTool
from tools.search_tool import SearchTool

logger = logging.getLogger("swariva.tools.registry")


class ToolRegistry:
    """Central registry and router for all SWARIVA real-time tools."""

    def __init__(self):
        self.tools: List[BaseTool] = [
            WeatherTool(),
            GoldPriceTool(),
            ReminderTool(),
            SearchTool(),
        ]

    def find_tool(self, query: str) -> Optional[BaseTool]:
        """Finds the first tool matching the query intent."""
        for tool in self.tools:
            if tool.can_handle(query):
                return tool
        return None

    async def execute_matching_tool(
        self, query: str, context: Optional[Dict[str, Any]] = None
    ) -> Optional[ToolResult]:
        """
        Executes a matching tool if query demands real-time data.
        Returns ToolResult or None if no tool is required.
        """
        tool = self.find_tool(query)
        if not tool:
            return None

        logger.info("Routing query to tool '%s': %s", tool.name, query[:50])
        try:
            return await tool.execute(query, context=context)
        except Exception as e:
            logger.error("Error executing tool '%s': %s", tool.name, e)
            return None


# Global singleton instance
tool_registry = ToolRegistry()
