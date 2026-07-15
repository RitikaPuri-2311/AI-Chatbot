# AI Customer Support Chatbot

A full-stack **AI Customer Support Assistant** that combines a Next.js chat interface with a FastAPI backend powered by **Google Gemini**, **LangGraph**, **RAG (ChromaDB)**, and mock support tools for order lookup, ticketing, and escalation.

Users can chat with multiple personas, upload PDF knowledge-base documents, query them with citations, browse **Company FAQ** policies, check **live weather** by city, and manage conversations via REST APIs.

---

## Project Overview

This project is an end-to-end customer support platform:

- **Frontend** — Next.js 16 App Router UI with login/register, streaming chat, document panel, and Company FAQ mode (quick-action chips + welcome card).
- **Backend** — FastAPI API with JWT authentication, PostgreSQL persistence, optional Redis conversation cache, ChromaDB vector search, and a LangGraph agent that routes requests to RAG retrieval or support tools.
- **Agent** — A stateful LangGraph workflow classifies each message, runs document search / FAQ lookup / support tools in a loop, and generates grounded answers with page-level citations.

The system supports two conversation tracks:

| Track | Storage | Used by |
|-------|---------|---------|
| **Chat sessions** | `chat_sessions` + `messages` (PostgreSQL), Redis cache | Frontend chat UI (`/api/chat/*`) |
| **Support conversations** | `conversations` + `conversation_messages` (PostgreSQL) | Conversation APIs (`/api/conversations/*`) |

Document-agent queries (`/api/documents/query`) run through LangGraph and optionally persist turn history in Redis when a `session_id` is provided.

---

## Key Features

### AI Customer Support Assistant
Gemini-powered assistant with configurable personas (`default`, `support`, `code_reviewer`, `document_analyst`). The support persona is integrated with LangGraph for tool use and knowledge-base retrieval.

### LangGraph Workflow
Stateful agent graph with routing, tool loops, checkpointing (`MemorySaver`), and a `generate_answer` node that appends citations.

### Company FAQ RAG
Policy questions (returns, warranty, shipping, cancellation, business hours, contact info) are detected via `company_faq.py` and searched against uploaded `Company_FAQ.pdf` without manual document selection. The frontend **Company FAQ** mode sends `faq_mode: true` to force FAQ routing.

### Weather Lookup
Weather questions (current conditions, temperature, rain) are detected via `weather_service.py` and routed to a dedicated **`weather`** LangGraph node. The **Weather** persona sends `weather_mode: true` to force weather routing. Data comes from the [OpenWeatherMap Current Weather API](https://openweathermap.org/current); set `OPENWEATHER_API_KEY` in `Backend/.env`.

Example prompts:
- `What's the weather in Delhi?`
- `Weather in Mumbai`
- `Temperature in Bangalore`
- `Will it rain today in Chennai?`

### Document Upload & Search
PDF upload, text extraction (PyMuPDF), chunking, embedding (`all-MiniLM-L6-v2`), and per-user ChromaDB collections. Supports single-document, multi-document, compare, and metadata query modes.

### Order Status Tool
Mock `check_order_status` tool — looks up orders such as `ORD-10001`, `ORD-10002`, `ORD-10003` with sample statuses (Processing, Shipped, Delivered).

### Create Support Ticket
Mock `create_ticket` tool — returns generated ticket IDs (e.g. `SUP-101`).

### Escalate to Human
Mock `escalate_to_human` tool — returns escalation IDs (e.g. `ESC-201`).

### Intent Classification
Keyword-based `classify_intent` support tool plus LLM-based query routing in `routing.py`. Intents include FAQ, Order Status, Refund, Complaint, Technical Support, and General Inquiry.

### Conversation History
- Chat UI: session list, message history, export (`/api/chat/sessions`, `/api/chat/history/{id}`).
- Support API: CRUD conversations with stored intent, tools used, and response time metadata.

### Authentication
JWT bearer auth with role-style permissions (`ai:chat`, `ai:embed`, `ai:search`). Register, login, and `/me` endpoints.

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | Next.js 16, React 19, TypeScript, Tailwind CSS 4 |
| **Backend** | FastAPI, Uvicorn, Pydantic |
| **AI / Agent** | Google Gemini (`google-genai`), LangGraph, LangChain text splitter |
| **Embeddings / RAG** | sentence-transformers (`all-MiniLM-L6-v2`), ChromaDB |
| **PDF processing** | PyMuPDF (`fitz`) |
| **Database** | PostgreSQL (async SQLAlchemy + asyncpg), Alembic migrations |
| **Cache** | Redis (optional, chat history sliding window) |
| **Auth** | python-jose (JWT), passlib + bcrypt |
| **Testing** | pytest, pytest-asyncio, httpx, SQLite (aiosqlite) for tests |

> **Note:** `chromadb`, `redis`, `PyMuPDF`, `sentence-transformers`, and `langchain` are imported by the backend services. Ensure they are installed in your Python environment alongside `requirements.txt`.

---

## System Architecture

```mermaid
flowchart TB
    subgraph frontend ["Frontend (Next.js)"]
        ui["Chat, Documents, FAQ UI"]
        auth_ui["Login and Register"]
    end

    subgraph backend ["Backend (FastAPI)"]
        auth_r["POST /api/auth"]
        chat_r["POST /api/chat"]
        doc_r["POST /api/documents"]
        conv_r["POST /api/conversations"]
    end

    subgraph agent ["LangGraph Agent"]
        classify["classify_route"]
        router_node["router"]
        rag_nodes["RAG and FAQ nodes"]
        support_nodes["Support tool nodes"]
        weather_node["weather node"]
        gen["generate_answer"]
    end

    subgraph data ["Data Layer"]
        pg[("PostgreSQL")]
        redis_db[("Redis")]
        chroma[("ChromaDB")]
    end

    subgraph external ["External APIs"]
        gemini["Google Gemini"]
        openweather["OpenWeatherMap"]
    end

    ui --> auth_r
    ui --> chat_r
    ui --> doc_r
    ui --> conv_r

    chat_r --> gemini
    chat_r --> pg
    chat_r --> redis_db

    doc_r --> classify
    conv_r --> classify
    conv_r --> pg

    classify --> router_node
    classify --> weather_node
    router_node --> rag_nodes
    router_node --> support_nodes
    rag_nodes --> chroma
    rag_nodes --> router_node
    support_nodes --> router_node
    weather_node --> openweather
    weather_node --> router_node
    router_node --> gen
    gen --> gemini

    doc_r --> pg
    doc_r --> chroma
    doc_r --> redis_db
```

---

## Project Folder Structure

```
AI-Chatbot/
├── Backend/
│   ├── alembic/                 # Database migrations
│   ├── app/
│   │   ├── graph/               # LangGraph workflow (nodes, routing, state, prompts)
│   │   ├── models/              # SQLAlchemy models (user, session, message, document, conversation)
│   │   ├── routers/             # FastAPI route handlers
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   ├── services/            # Business logic (RAG, agent, auth, support tools, weather)
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── dependencies.py
│   │   └── main.py
│   ├── tests/                   # pytest suites
│   ├── requirements.txt
│   └── pytest.ini
│
├── Frontend/
│   ├── app/
│   │   ├── (auth)/login/        # Login page
│   │   ├── (auth)/register/     # Register page
│   │   ├── chat/                # Main chat + sidebar (Documents, FAQ)
│   │   ├── layout.tsx
│   │   └── globals.css
│   ├── components/
│   │   ├── auth/                # Login/register forms
│   │   ├── chat/                # Chat window, bubbles, input
│   │   ├── documents/           # Document panel, sources
│   │   ├── faq/                 # Company FAQ UI
│   │   └── weather/             # Weather persona quick-action chips
│   ├── hooks/                   # useAuth
│   ├── lib/                     # api.ts, auth.ts
│   ├── types/                   # Shared TypeScript types
│   └── middleware.ts
│
└── README.md
```

---

## Installation & Setup

### Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.11+
- **PostgreSQL**
- **Redis** (optional but recommended for chat history cache)
- **Google Gemini API key**

### Backend

```bash
cd Backend
python -m venv venv

# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
pip install chromadb redis PyMuPDF sentence-transformers langchain
```

Create `Backend/.env` (see [Environment Variables](#environment-variables)):

```bash
# Copy and edit — do not commit secrets
cp .env.example .env   # if you maintain an example file
```

Run database migrations (optional; tables are also created on startup):

```bash
python -m alembic upgrade head
```

Start the API:

```bash
uvicorn app.main:app --reload --port 8000
```

API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### Frontend

```bash
cd Frontend
npm install
npm run dev
```

App URL: [http://localhost:3000](http://localhost:3000) (redirects to `/login`).

### Database

PostgreSQL connection string format (async):

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/chatbot_db
```

**Tables created by the application:**

| Table | Purpose |
|-------|---------|
| `users` | Accounts, hashed passwords, permissions |
| `chat_sessions` | Legacy chat sessions for UI |
| `messages` | Legacy chat messages |
| `documents` | Uploaded PDF metadata |
| `conversations` | Support conversation records |
| `conversation_messages` | Support messages with intent / tool metadata |

Alembic migration `001_add_conversation_tables` adds `conversations` and `conversation_messages`.

---

## Environment Variables

Example `Backend/.env`:

```env
# Google Gemini
GOOGLE_API_KEY=your_gemini_api_key

# JWT
SECRET_KEY=your_long_random_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# PostgreSQL (async driver)
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/ai_chatbot

# Redis (optional — chat history cache)
REDIS_URL=redis://localhost:6379
REDIS_TTL=86400

# OpenWeatherMap (optional — weather persona / weather routing)
OPENWEATHER_API_KEY=your_openweather_api_key
```

The frontend calls the API at `http://localhost:8000` (configured in `Frontend/lib/api.ts`).

---

## Running the Project

**Terminal 1 — Backend:**

```bash
cd Backend
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 — Frontend:**

```bash
cd Frontend
npm run dev
```

**Terminal 3 — Redis (optional):**

```bash
redis-server
```

**Typical flow:**

1. Register at `/register` and log in.
2. Upload PDFs (including `Company_FAQ.pdf` for FAQ mode) via the Documents sidebar.
3. Chat in default/support persona, query documents, or open **Company FAQ**.

---

## API Overview

Base URL: `http://localhost:8000/api`  
Authentication: `Authorization: Bearer <accessToken>` unless noted.

### Auth — `/api/auth`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/auth/register` | Register user; returns `accessToken` + user |
| `POST` | `/auth/login` | Login; returns `accessToken` + user |
| `GET` | `/auth/me` | Current user profile (requires JWT) |

Default permissions on register: `ai:chat`, `ai:embed`, `ai:search`.

### Documents — `/api/documents`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/documents/upload` | Upload and index a PDF |
| `GET` | `/documents/` | List user's documents |
| `DELETE` | `/documents/{document_id}` | Delete document and vectors |
| `POST` | `/documents/query` | Run LangGraph agent (optional `document_id`, `session_id`, `faq_mode`, `stream`) |
| `GET` | `/documents/{document_id}/export` | Export document text |

**Query body example:**

```json
{
  "question": "What is your return policy?",
  "document_id": null,
  "session_id": "optional-session-uuid",
  "stream": false,
  "faq_mode": true
}
```

### Customer Support (Chat) — `/api/chat`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/chat/` | Non-streaming chat (requires `ai:chat`) |
| `POST` | `/chat/stream` | SSE streaming chat with persona |
| `GET` | `/chat/sessions` | List chat sessions |
| `POST` | `/chat/sessions` | Create chat session |
| `PATCH` | `/chat/sessions/{session_id}` | Rename session |
| `DELETE` | `/chat/sessions/{session_id}` | Delete session + Redis cache |
| `GET` | `/chat/history/{session_id}` | Message history |
| `GET` | `/chat/sessions/{session_id}/export` | Plain-text export |

### Conversations — `/api/conversations`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/conversations` | Create support conversation (`title`, `persona`) |
| `POST` | `/conversations/{id}/messages` | Add user message → run agent → save assistant reply |
| `GET` | `/conversations/{id}` | Full conversation history |
| `DELETE` | `/conversations/{id}` | Delete conversation and messages |

**Add message body:**

```json
{
  "role": "user",
  "content": "Where is my order ORD-10002?"
}
```

Assistant metadata stored: `intent`, `tool_used`, `response_time_ms`.

### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | `{ "status": "ok" }` |

---

## LangGraph Workflow

The customer support agent is compiled in `Backend/app/graph/graph.py` with **MemorySaver** checkpointing (`thread_id = doc:{session_id}`).

### Query modes (`AgentState.query_mode`)

| Mode | Entry node | Purpose |
|------|------------|---------|
| `normal_chat` | `normal_chat` | General conversation |
| `single_document` | `single_document_search` | Search one document |
| `multi_document` | `multi_document_search` | Search all user documents |
| `compare` | `compare_documents` | Compare two documents |
| `metadata` | `metadata` | Document info / page listing |
| `support` | `support_entry` | Support tool routing |
| `company_faq` | `company_faq_search` | Company FAQ policy RAG |
| `weather` | `weather` | Current weather via OpenWeatherMap |

### Flow (simplified)

1. **`classify_route`** — LLM + heuristics pick query mode; detect support requests, FAQ policy questions, and weather prompts.
2. **Mode entry node** — Proactive RAG search, support entry, or weather fetch as needed.
3. **`router`** — Gemini function calling; enqueues tools (`search_document`, `check_order_status`, `get_weather`, etc.).
4. **Tool nodes** — Execute RAG, support, or weather tools; return to `router` until done.
5. **`generate_answer`** — Final Gemini response with **References** footer and structured `sources`.

### RAG tools (router)

- `search_document`
- `compare_documents`
- `get_document_info`
- `list_pages`

### Support tools (router)

- `classify_intent`
- `check_order_status`
- `create_ticket`
- `escalate_to_human`

### Weather tools (router + weather node)

- `get_weather` — Current conditions for a city (`weather_service.py` → OpenWeatherMap)

Gemini declarations: `Backend/app/graph/weather_tool_defs.py`. The **`weather`** node proactively calls `get_weather`, injects structured results into the conversation, then routes to **`router`** → **`generate_answer`** for a natural reply.

---

## RAG Pipeline

Implemented in `Backend/app/services/rag_service.py`.

1. **Upload** — PDF saved under `Backend/uploads/`; metadata stored in PostgreSQL `documents` table.
2. **Extract** — PyMuPDF extracts text per page.
3. **Chunk** — `RecursiveCharacterTextSplitter` (512 chars, 50 overlap).
4. **Embed** — `SentenceTransformer('all-MiniLM-L6-v2')`.
5. **Store** — ChromaDB persistent client (`./documents_chroma_db`), **one collection per user** (`user_{user_id}`).
6. **Search** — Cosine similarity query; optional `document_id` metadata filter.
7. **Cite** — Retrieved chunks flow into `AgentState.retrieved_chunks` and appear in API `sources` with filename, page, snippet, and similarity.

**Company FAQ** (`company_faq.py`) resolves `Company_FAQ.pdf` by filename and scopes policy questions to that document automatically.

---

## Customer Support Tools

Mock implementations in `Backend/app/services/support_tools.py` — designed to be swapped for real integrations (Jira, OMS, escalation queues).

| Tool | Description |
|------|-------------|
| **`classify_intent`** | Keyword classifier → FAQ, Order Status, Refund, Complaint, Technical Support, General Inquiry |
| **`check_order_status`** | Mock lookup for `ORD-*` IDs |
| **`create_ticket`** | Mock ticket creation → `SUP-{n}` |
| **`escalate_to_human`** | Mock escalation → `ESC-{n}` |

Gemini function declarations live in `Backend/app/graph/support_tool_defs.py`. The router uses `FunctionCallingConfigMode.ANY` on support paths so tools are invoked instead of hallucinating unavailable actions.

**Disambiguation:** Policy questions (e.g. “refund policy”) route to FAQ RAG; action requests (e.g. “I want a refund”) route to support tools.

---

## Screenshots

> Add screenshots to `docs/screenshots/` and replace the placeholders below.

| Screenshot | Description |
|--------------|-------------|
| ![Chat UI](docs/screenshots/chat.png) | Main chat interface with sessions sidebar |
| ![Documents](docs/screenshots/documents.png) | Document upload and scoped search |
| ![Company FAQ](docs/screenshots/faq.png) | Company FAQ mode with quick-action chips |
| ![API Docs](docs/screenshots/swagger.png) | FastAPI Swagger UI at `/docs` |

---

## Testing

### pytest

From `Backend/`:

```bash
pytest
```

Run specific suites:

```bash
pytest tests/test_auth.py -v
pytest tests/test_chat.py tests/test_chatbot.py -v
pytest tests/test_documents.py -v
pytest tests/test_conversations.py -v
```

Tests use **SQLite** (`tests/conftest.py`) with dependency overrides — no PostgreSQL required for CI/local test runs. Conversation tests **mock** the LangGraph agent (`invoke_support_agent`) to avoid real LLM calls.

| Test file | Coverage |
|-----------|----------|
| `test_auth.py` | Register, login, `/me`, health |
| `test_chat.py` | Auth guards, session CRUD |
| `test_chatbot.py` | Streaming, export, personas |
| `test_documents.py` | Upload, list, query, isolation |
| `test_conversations.py` | Conversation CRUD + messaging |

### Coverage (optional)

`pytest-cov` is not pinned in `requirements.txt`. To measure coverage:

```bash
pip install pytest-cov
pytest --cov=app --cov-report=term-missing
```

---

## Future Enhancements

Based on current code comments and architecture gaps:

- Replace mock support tools with real **order management**, **ticketing** (Jira/Zendesk), and **human escalation** queue APIs.
- Swap the keyword **intent** classifier for an LLM-based model.
- **httpOnly cookie** auth instead of `localStorage` JWT (noted in frontend rules).
- **Token refresh** and production-hardened auth.
- Pin missing runtime dependencies (`chromadb`, `redis`, etc.) explicitly in `requirements.txt`.
- Markdown rendering for AI responses, session sidebar for multi-FAQ sources, and mobile layout polish.

---

## License

No license file is included in this repository. Add a `LICENSE` file (e.g. MIT) before public distribution.

---

## Quick Reference

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| OpenAPI docs | http://localhost:8000/docs |
| Health check | http://localhost:8000/ |

**Default test credentials:** Register a new account via the UI or `POST /api/auth/register`.

**Sample mock orders:** `ORD-10001`, `ORD-10002`, `ORD-10003`

**Company FAQ document:** Upload `Company_FAQ.pdf` for automatic policy RAG.
