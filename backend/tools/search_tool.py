"""
SWARIVA AI — Live Web Fact Search Tool
Provides fast real-time summary lookups using DuckDuckGo Instant Answer API.
Used as a RAG fallback for factual queries outside the static knowledge base.
"""
import logging
from typing import Dict, Any, Optional
import httpx

from tools.base import BaseTool, ToolResult

logger = logging.getLogger("swariva.tools.search")


class SearchTool(BaseTool):
    """Tool for retrieving web facts and encyclopedic answers."""

    name = "search_tool"
    description = "Searches for real-time facts and encyclopedic definitions."

    TRIGGER_WORDS = [
        "search for", "who is", "what is the capital", "population of", "latest news",
        "వెతకండి", "ఎవరు", "రాజధాని",
        "सर्च करो", "कौन है", "राजधानी क्या है"
    ]

    def can_handle(self, query: str) -> bool:
        lower = query.lower()
        return any(term in lower for term in self.TRIGGER_WORDS)

    async def execute(self, query: str, context: Optional[Dict[str, Any]] = None) -> ToolResult:
        clean_q = query.strip()
        url = "https://api.duckduckgo.com/"
        params = {
            "q": clean_q,
            "format": "json",
            "no_html": "1",
            "skip_disambig": "1",
        }

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(url, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    abstract = data.get("AbstractText") or data.get("Answer")
                    if abstract:
                        en = f"According to online reference: {abstract}"
                        te = f"ఆన్‌లైన్ సమాచారం ప్రకారం: {abstract}"
                        hi = f"ऑनलाइन संदर्भ के अनुसार: {abstract}"
                        return ToolResult(
                            success=True,
                            tool_name=self.name,
                            data={"abstract": abstract, "source": data.get("AbstractSource", "Web")},
                            spoken_summary={"english": en, "telugu": te, "hindi": hi},
                            source="DuckDuckGo Instant Answer",
                        )
        except Exception as e:
            logger.info("Search lookup timed out or failed (%s)", e)

        return ToolResult(
            success=False,
            tool_name=self.name,
            data={"query": clean_q},
            spoken_summary={
                "english": f"I looked up information regarding {clean_q}.",
                "telugu": f"{clean_q} గురించి వివరాలను పరిశీలించాను.",
                "hindi": f"{clean_q} के संदर्भ में जानकारी प्राप्त की।",
            },
            source="Search Fallback",
        )
