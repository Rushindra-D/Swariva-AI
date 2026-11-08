# 🛠️ Real-Time Tool Calling & RAG Pipeline Specification

To prevent factual hallucinations in voice interactions, SWARIVA AI incorporates a zero-latency **Tool Calling & Retrieval-Augmented Generation (RAG)** pipeline.

---

## 1. Tool Architecture

All tools inherit from `BaseTool` (`backend/tools/base.py`) and are dispatched by `ToolRegistry` (`backend/tools/registry.py`):

```python
@dataclass
class ToolResult:
    success: bool
    tool_name: str
    data: Dict[str, Any]
    spoken_summary: Dict[str, str]  # Multilingual: English, Telugu, Hindi
    source: str
    error: Optional[str] = None
```

---

## 2. Implemented Tools

### 2.1 Weather Tool (`backend/tools/weather_tool.py`)
- **Data Source:** Open-Meteo Free API (`https://api.open-meteo.com/v1/forecast`)
- **Authentication:** None required (100% free and open)
- **Supported Cities:** Hyderabad, Bengaluru, Delhi, Mumbai, Chennai, Kolkata, Vijayawada, Visakhapatnam, Tirupati, Warangal.
- **Output:** Live temperature (°C), weather condition, humidity (%), wind speed (km/h).
- **Spoken Delivery:** Automatically generated spoken sentences in Telugu, Hindi, and English.

### 2.2 Gold Price Tool (`backend/tools/gold_price_tool.py`)
- **Data Source:** Hyderabad / Indian Bullion Market financial feed with baseline cache.
- **Metrics Tracked:**
  - 24 Karat (99.9% Pure) gold rate per gram and per 10 grams (tola).
  - 22 Karat (Jewellery hallmark) gold rate per gram and per 10 grams.
  - Silver rate per gram and per kilogram.
- **Spoken Delivery:** Formatted with Indian numbering (lakhs/thousands) in Telugu, Hindi, and English.

### 2.3 Voice Reminders Tool (`backend/tools/reminder_tool.py`)
- **Data Source:** `ReminderRepository` (Supabase Cloud PostgreSQL or SQLite fallback).
- **Capabilities:**
  - Natural language reminder scheduling (e.g. "Remind me to take my blood pressure pills").
  - Reminder listing (e.g. "What are my reminders for today?").
- **Tenant Isolation:** Enforces user-scoped storage for authenticated profiles.

### 2.4 Web Search Tool (`backend/tools/search_tool.py`)
- **Data Source:** DuckDuckGo Instant Answer API.
- **Purpose:** Answers current affairs, encyclopedic definitions, and real-time facts outside the local knowledge base.

---

## 3. RAG Grounding Flow

1. When a query arrives at `agent.py`, `tool_registry.execute_matching_tool(query)` checks if real-time data is required.
2. If matched, the tool executes and produces a verified multilingual `ToolResult`.
3. If using an external LLM (Evon or Groq), the verified data is injected into the prompt as `VERIFIED REAL-TIME DATA (GROUND TRUTH)`.
4. If using the offline `KnowledgeCompanionProvider`, the tool's verified spoken text is returned directly, ensuring **zero latency** and **100% factual accuracy**.

