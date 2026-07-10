# AI-Chatbot — Developer Notes

Quick reference for the **AI Customer Support Chatbot**. Full documentation: [README.md](./README.md).

---

## Project Folder Structure

```
AI-Chatbot/
├── README.md                     # Full project documentation
├── notes.md                      # This file — quick dev reference
├── .cursorrules                  # Frontend dev rules & conventions
│
├── Backend/
│   ├── alembic/                  # DB migrations (conversations tables)
│   ├── app/
│   │   ├── main.py               # FastAPI entry — registers all routers
│   │   ├── config.py             # .env settings
│   │   ├── database.py           # Async SQLAlchemy + create_tables
│   │   ├── dependencies.py       # JWT auth + require_permission()
│   │   │
│   │   ├── graph/                # LangGraph agent workflow
│   │   │   ├── graph.py          # StateGraph compile + run_document_graph()
│   │   │   ├── nodes.py          # All graph nodes + tool dispatch
│   │   │   ├── routing.py        # LLM query-mode classifier
│   │   │   ├── state.py          # AgentState TypedDict
│   │   │   ├── prompts.py        # System prompts
│   │   │   ├── support_tool_defs.py
│   │   │   └── contents.py
│   │   │
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── session.py        # ChatSession (chat_sessions)
│   │   │   ├── message.py        # Message + ConversationMessage
│   │   │   ├── document.py
│   │   │   └── conversation.py   # Support conversations
│   │   │
│   │   ├── routers/
│   │   │   ├── auth.py           # /api/auth
│   │   │   ├── chat.py           # /api/chat
│   │   │   ├── documents.py      # /api/documents
│   │   │   ├── conversations.py  # /api/conversations
│   │   │   └── analytics.py      # /api/analytics
│   │   │
│   │   ├── schemas/              # Pydantic models (conversation, analytics)
│   │   ├── services/
│   │   │   ├── auth_service.py
│   │   │   ├── gemini_service.py # Streaming chat + personas
│   │   │   ├── redis_service.py
│   │   │   ├── rag_service.py    # ChromaDB RAG pipeline
│   │   │   ├── agent_service.py  # Facade → run_document_graph()
│   │   │   ├── support_tools.py  # Mock support tools
│   │   │   ├── company_faq.py    # FAQ policy detection + doc resolve
│   │   │   ├── conversation_service.py
│   │   │   └── analytics_service.py
│   │   └── utils/
│   │       └── sentiment.py      # Keyword sentiment for analytics
│   │
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_auth.py
│   │   ├── test_chat.py
│   │   ├── test_chatbot.py
│   │   ├── test_documents.py
│   │   ├── test_conversations.py
│   │   └── test_analytics.py
│   │
│   ├── requirements.txt
│   └── pytest.ini
│
└── Frontend/
    ├── app/
    │   ├── (auth)/login/         # /login
    │   ├── (auth)/register/      # /register
    │   ├── chat/page.tsx         # Main UI — chat, docs, FAQ, analytics
    │   ├── layout.tsx
    │   └── globals.css
    │
    ├── components/
    │   ├── auth/                 # LoginForm, RegisterForm
    │   ├── chat/                 # ChatWindow, MessageBubble, MessageInput
    │   ├── documents/            # DocumentPanel, SourcePanel
    │   ├── faq/                  # FaqQuickChips, CompanyFaqWelcome
    │   ├── analytics/            # AnalyticsDashboard, SummaryCards, etc.
    │   └── ThemeProvider.tsx
    │
    ├── hooks/useAuth.ts
    ├── lib/api.ts                # All API calls
    ├── lib/auth.ts
    ├── lib/citations.ts          # Strip duplicate refs, group sources
    ├── types/index.ts
    └── middleware.ts             # / → /login redirect
```

---

## Excluded (generated / local only)

| Path | Purpose |
|------|---------|
| `Backend/venv/` | Python virtual environment |
| `Backend/.pytest_cache/` | Pytest cache |
| `Backend/test.db` | SQLite test database |
| `Backend/uploads/` | Uploaded PDF files |
| `Backend/documents_chroma_db/` | ChromaDB persistent store |
| `Backend/**/__pycache__/` | Python bytecode |
| `Frontend/node_modules/` | npm dependencies |
| `Frontend/.next/` | Next.js build output |

---

## Tech Stack

| Layer | Stack |
|-------|-------|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS 4 |
| Backend | FastAPI, SQLAlchemy (async), PostgreSQL |
| AI | Google Gemini (`gemini-3.1-flash-lite` chat, `gemini-2.0-flash` classifier) |
| Agent | LangGraph + MemorySaver checkpointing |
| RAG | ChromaDB, sentence-transformers, PyMuPDF, LangChain splitter |
| Cache | Redis (optional — chat history) |
| Auth | JWT in `localStorage` (frontend), Bearer token (API) |
| Migrations | Alembic |
| Tests | pytest, pytest-asyncio, httpx, aiosqlite |

---

## How to Run

```bash
# Backend (port 8000)
cd Backend
uvicorn app.main:app --reload --port 8000

# Frontend (port 3000)
cd Frontend
npm run dev

# Migrations (optional — tables also created on startup)
cd Backend
python -m alembic upgrade head

# Tests
cd Backend
pytest
pytest tests/test_conversations.py tests/test_analytics.py -v
pytest --cov=app --cov-report=term-missing   # requires pytest-cov
```

---

## Environment Variables (`Backend/.env`)

```env
GOOGLE_API_KEY=
SECRET_KEY=
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/ai_chatbot
REDIS_URL=redis://localhost:6379
REDIS_TTL=86400
```

---

## Frontend Routes & Sidebar Modes

| URL / Mode | Description |
|------------|-------------|
| `/` | Redirects to `/login` |
| `/login` | Login |
| `/register` | Register |
| `/chat` | Main app (sidebar modes below) |
| **Chats** tab | Session list + streaming chat |
| **Documents** tab | Upload PDFs, scope search (single / all) |
| **Company FAQ** | `faq_mode: true` → policy RAG on `Company_FAQ.pdf` |
| **Analytics** | Dashboard — overview, topics, sentiment |

**Personas (chat mode):** `default`, `support`, `code_reviewer`, `document_analyst`

---

## API Endpoints (base: `http://localhost:8000/api`)

### Auth — `/auth`
| Method | Path | Notes |
|--------|------|-------|
| POST | `/auth/register` | Returns `accessToken` |
| POST | `/auth/login` | Returns `accessToken` |
| GET | `/auth/me` | Current user |

### Chat — `/chat` (frontend UI)
| Method | Path | Notes |
|--------|------|-------|
| POST | `/chat/stream` | SSE streaming + persona |
| GET/POST | `/chat/sessions` | List / create |
| GET | `/chat/history/{session_id}` | Messages |
| DELETE | `/chat/sessions/{id}` | Delete + clear Redis |

### Documents — `/documents` (LangGraph agent)
| Method | Path | Notes |
|--------|------|-------|
| POST | `/documents/upload` | PDF only |
| GET | `/documents/` | List |
| POST | `/documents/query` | `faq_mode`, `document_id`, `session_id`, `stream` |
| DELETE | `/documents/{id}` | Delete + vectors |

### Conversations — `/conversations` (support API + analytics source)
| Method | Path | Notes |
|--------|------|-------|
| POST | `/conversations` | `{ title, persona }` |
| POST | `/conversations/{id}/messages` | User msg → agent → assistant reply |
| GET | `/conversations/{id}` | History with timestamps |
| DELETE | `/conversations/{id}` | Cascade delete messages |

### Analytics — `/analytics`
| Method | Path | Returns |
|--------|------|---------|
| GET | `/analytics/conversations` | totals, avg duration, avg messages, top persona |
| GET | `/analytics/topics` | intent counts |
| GET | `/analytics/sentiment` | positive / neutral / negative |

All protected routes need `Authorization: Bearer <token>` and `ai:chat` permission where enforced.

---

## Database Tables

| Table | Used by |
|-------|---------|
| `users` | Auth |
| `chat_sessions` + `messages` | Frontend chat UI |
| `documents` | PDF metadata |
| `conversations` + `conversation_messages` | Support API + analytics |

---

## LangGraph Query Modes

| Mode | Entry node | When |
|------|------------|------|
| `normal_chat` | `normal_chat` | General chat |
| `single_document` | `single_document_search` | One doc scoped |
| `multi_document` | `multi_document_search` | All user docs |
| `compare` | `compare_documents` | Two-doc compare |
| `metadata` | `metadata` | Doc info / pages |
| `support` | `support_entry` | Order, ticket, escalation |
| `company_faq` | `company_faq_search` | Policy questions / `faq_mode` |

**Flow:** `classify_route` → mode node → `router` ↔ tools → `generate_answer`

**RAG tools:** `search_document`, `compare_documents`, `get_document_info`, `list_pages`

**Support tools:** `classify_intent`, `check_order_status`, `create_ticket`, `escalate_to_human`

---

## RAG Pipeline (short)

1. Upload PDF → `uploads/`
2. PyMuPDF extract → chunk (512/50) → embed (`all-MiniLM-L6-v2`)
3. Store in Chroma (`documents_chroma_db/`, one collection per user)
4. Search → chunks → citations in `sources` array

**Company FAQ:** upload `Company_FAQ.pdf` — policy questions auto-route without picking a doc.

---

## Mock Support Data

| Type | Examples |
|------|----------|
| Orders | `ORD-10001` Processing, `ORD-10002` Shipped, `ORD-10003` Delivered |
| Tickets | `SUP-101`, `SUP-102`, … |
| Escalations | `ESC-201`, `ESC-202`, … |

**Intent categories:** FAQ, Order Status, Refund, Complaint, Technical Support, General Inquiry

---

## Two Conversation Tracks

| Track | API | Storage | Analytics |
|-------|-----|---------|-----------|
| Chat UI | `/api/chat/*` | `chat_sessions`, `messages`, Redis | No |
| Support API | `/api/conversations/*` | `conversations`, `conversation_messages` | Yes |

Document queries (`/api/documents/query`) use LangGraph + optional Redis history — not the conversations table.

---

## Useful Files When Debugging

| Issue | Check |
|-------|-------|
| Agent not calling tools | `graph/nodes.py` router, `support_tools.py` |
| Wrong routing | `graph/routing.py`, `company_faq.py` |
| FAQ not working | `Company_FAQ.pdf` uploaded? `faq_mode` from frontend? |
| Empty analytics | Data lives in `conversations` table — create via `/api/conversations` |
| Citations duplicated | `Frontend/lib/citations.ts` + `SourcePanel.tsx` |
| Compare docs fails | `routing.py` `resolve_compare_document_ids_from_names` |

---

## Test Credentials

Register via UI or API — no hardcoded users. Use mock order IDs above for support tool demos.
