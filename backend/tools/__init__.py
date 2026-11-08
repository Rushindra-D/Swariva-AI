"""
SWARIVA AI — Tools Package
Exports BaseTool, ToolResult, ToolRegistry, and tool_registry singleton.
"""
from tools.base import BaseTool, ToolResult
from tools.weather_tool import WeatherTool
from tools.gold_price_tool import GoldPriceTool
from tools.reminder_tool import ReminderTool
from tools.search_tool import SearchTool
from tools.registry import ToolRegistry, tool_registry

__all__ = [
    "BaseTool",
    "ToolResult",
    "WeatherTool",
    "GoldPriceTool",
    "ReminderTool",
    "SearchTool",
    "ToolRegistry",
    "tool_registry",
]

