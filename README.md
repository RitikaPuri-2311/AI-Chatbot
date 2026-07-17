# AI Chatbot

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-16-black?logo=next.js&logoColor=white)](https://nextjs.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?logo=redis&logoColor=white)](https://redis.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A full-stack AI chatbot platform that combines a modern Next.js frontend with a FastAPI backend powered by **Google Gemini**, **LangGraph**, **ChromaDB**, **PostgreSQL**, and **Redis**. Users can hold streaming AI conversations, upload PDF documents for semantic search, query company FAQs, check live weather, and submit support tickets through a polished SaaS-style interface.

Built for production-style patterns: JWT authentication, role-based permissions, session-based chat history, RAG with citations, and Dockerized deployment.

---

## ✨ Features

- **AI-powered conversational chatbot** — Streaming responses via Google Gemini with multiple personas (`default`, `support`, `code_reviewer`, `document_analyst`)
- **Retrieval-Augmented Generation (RAG)** — PDF ingestion, chunking, embedding, and semantic search with page-level citations
- **Document upload and semantic search** — Per-user ChromaDB collections; single, multi-document, compare, and metadata query modes
- **JWT Authentication** — Secure register, login, and token-based API access
- **Role-Based Access Control (RBAC)** — Permission gates for `ai:chat`, `ai:embed`, and `ai:search`
- **Session-based chat history** — Create, rename, pin, export, and delete chat sessions with PostgreSQL + Redis caching
- **Weather API integration** — Live conditions via OpenWeatherMap, routed through the LangGraph agent
- **FAQ support** — Company policy Q&A against uploaded FAQ documents with dedicated UI mode
- **Help & Support module** — Jira issue creation, search, assignment, and status updates from the frontend
- **Redis caching** — Fast conversation history retrieval with configurable TTL
- **PostgreSQL database** — Persistent users, sessions, messages, documents, and support conversations
- **Dockerized deployment** — Multi-container setup with Docker Compose (API, frontend, PostgreSQL, Redis)
- **Responsive Next.js frontend** — Collapsible sidebar, dark mode, markdown rendering, chat history grouping, and mobile-friendly layout

---

## 🛠 Tech Stack

### Backend

| Technology | Purpose |
|------------|---------|
| Python 3.12+ | Runtime |
| FastAPI | REST API framework |
| SQLAlchemy | Async ORM |
| Alembic | Database migrations |
| PostgreSQL | Primary data store |
| Redis | Conversation cache |
| JWT (python-jose) | Authentication tokens |
| LangGraph | Agent orchestration & routing |
| ChromaDB | Vector store for RAG |
| Google Gemini API | LLM inference & classification |
| sentence-transformers | Document embeddings |
| PyMuPDF | PDF text extraction |

### Frontend

| Technology | Purpose |
|------------|---------|
| Next.js 16 | App Router framework |
| React 19 | UI library |
| TypeScript | Type-safe development |
| Tailwind CSS 4 | Utility-first styling |
| Lucide React | Icon system |
| react-markdown | AI response rendering |

### DevOps

| Technology | Purpose |
|------------|---------|
| Docker | Container runtime |
| Docker Compose | Multi-service orchestration |
| AWS EC2 | Cloud deployment target |
| Git | Version control |
| GitHub | Repository hosting |

---

## 📁 Project Structure

```
AI-Chatbot/
├── Backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app entry point
│   │   ├── config.py               # Environment settings
│   │   ├── database.py             # SQLAlchemy engine & sessions
│   │   ├── dependencies.py         # JWT auth & RBAC guards
│   │   ├── routers/                # API route handlers
│   │   │   ├── auth.py
│   │   │   ├── chat.py
│   │   │   ├── documents.py
│   │   │   ├── conversations.py
│   │   │   └── jira.py
│   │   ├── services/               # Business logic layer
│   │   │   ├── agent_service.py
│   │   │   ├── rag_service.py
│   │   │   ├── gemini_service.py
│   │   │   ├── weather_service.py
│   │   │   ├── jira_service.py
│   │   │   ├── redis_service.py
│   │   │   └── auth_service.py
│   │   ├── models/                 # SQLAlchemy ORM models
│   │   │   ├── user.py
│   │   │   ├── session.py
│   │   │   ├── message.py
│   │   │   ├── document.py
│   │   │   └── conversation.py
│   │   ├── schemas/                # Pydantic request/response models
│   │   │   ├── conversation.py
│   │   │   └── jira.py
│   │   └── graph/                  # LangGraph agent workflow
│   │       ├── graph.py
│   │       ├── nodes.py
│   │       ├── routing.py
│   │       ├── prompts.py
│   │       └── state.py
│   ├── alembic/                    # Database migration scripts
│   ├── tests/                      # Pytest test suite
│   ├── requirements.txt
│   └── Dockerfile
├── Frontend/
│   ├── app/                        # Next.js App Router pages
│   │   ├── (auth)/login/
│   │   ├── (auth)/register/
│   │   ├── chat/
│   │   ├── documents/
│   │   ├── faq/
│   │   └── help-support/
│   ├── components/                 # React UI components
│   │   ├── auth/
│   │   ├── chat/
│   │   ├── documents/
│   │   ├── faq/
│   │   ├── help-support/
│   │   ├── layout/
│   │   └── ui/
│   ├── lib/                        # API client, auth, utilities
│   ├── hooks/                      # Custom React hooks
│   ├── types/                      # Shared TypeScript types
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## 🏗 System Architecture

The platform follows a layered architecture where the Next.js frontend communicates with the FastAPI backend, which orchestrates AI workflows through LangGraph and persists data across PostgreSQL, Redis, and ChromaDB.

```
┌─────────────────────────────────────────────────────────────────┐
│                         Next.js Frontend                        │
│          (Auth · AI Chat · Documents · FAQ · Support)           │
└───────────────────────────────┬─────────────────────────────────┘
                                │  HTTP / SSE
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend (REST)                     │
│     Auth · Chat · Documents · Conversations · Jira · Health     │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                ┌───────────────┴───────────────┐
                ▼                               ▼
┌───────────────────────────┐   ┌───────────────────────────────┐
│   Direct Gemini Stream    │   │      LangGraph Agent          │
│   (/api/chat/stream)      │   │   (/api/documents/query)      │
└───────────────┬───────────┘   └───────────────┬───────────────┘
                │                               │
                ▼                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Google Gemini API                          │
│              (chat, classification, generation)                 │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                ┌───────────────┼───────────────┐
                ▼               ▼               ▼
┌───────────────────┐ ┌─────────────────┐ ┌─────────────────────┐
│     ChromaDB      │ │   PostgreSQL    │ │       Redis         │
│  (vector / RAG)   │ │ users · sessions│ │  conversation cache │
│                   │ │ messages · docs │ │                     │
└───────────────────┘ └─────────────────┘ └─────────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  OpenWeatherMap API   │
                    │  (weather queries)    │
                    └───────────────────────┘
```

**Request flow summary:**

1. **AI Chat** — Frontend streams tokens from `/api/chat/stream`; Gemini generates responses; history is saved to PostgreSQL and cached in Redis.
2. **Document / FAQ / Weather queries** — Frontend calls `/api/documents/query`; LangGraph classifies intent, retrieves from ChromaDB or calls weather tools, then generates a grounded answer with citations.
3. **Help & Support** — Frontend submits Jira issues via `/api/jira/*` for ticket management.

---

## 🚀 Installation

### Prerequisites

- Python 3.12+ (3.14 supported with pinned dependencies)
- Node.js 20+
- PostgreSQL 16
- Redis 7
- Google Gemini API key

### Clone Repository

```bash
git clone https://github.com/RitikaPuri-2311/AI-Chatbot.git
cd AI-Chatbot
```

### Backend

```bash
# Create and activate a virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# Install dependencies
cd Backend
pip install -r requirements.txt

# Create environment file
# Copy the variables listed in the Environment Variables section into Backend/.env

# Start PostgreSQL and Redis (local or Docker), then run the API
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

**Example `Backend/.env`:**

```env
DATABASE_URL=postgresql+asyncpg://postgres:yourpassword@localhost:5432/chatbot_db
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
GOOGLE_API_KEY=your_google_gemini_api_key
OPENWEATHER_API_KEY=your_openweather_api_key
```

### Frontend

```bash
cd Frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:3000`.

---

## 🐳 Docker Setup

Docker Compose builds and runs all four services together. Ensure `Backend/.env` exists before starting.

```bash
# Build and start all containers
docker compose up --build

# Stop and remove containers
docker compose down

# View running services
docker compose ps
```

| Container | Service | Port |
|-----------|---------|------|
| `chatbot-frontend` | Next.js UI | `3000` |
| `chatbot-api` | FastAPI backend | `8000` |
| `chatbot-db` | PostgreSQL 16 | `5432` |
| `chatbot-redis` | Redis 7 | `6379` |

Set `POSTGRES_PASSWORD` in a root `.env` file or export it before running Compose — it is used by the `db` service.

---

## 🔐 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | Async PostgreSQL connection string (`postgresql+asyncpg://...`) |
| `REDIS_URL` | Yes | Redis connection URL (default: `redis://localhost:6379`) |
| `SECRET_KEY` | Yes | JWT signing secret — use a long random string in production |
| `ALGORITHM` | No | JWT algorithm (default: `HS256`) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | Token lifetime in minutes (default: `30`) |
| `GOOGLE_API_KEY` | Yes | Google Gemini API key for chat and agent routing |
| `OPENWEATHER_API_KEY` | No | OpenWeatherMap API key for weather queries |
| `REDIS_TTL` | No | Redis cache TTL in seconds (default: `86400`) |
| `JIRA_BASE_URL` | No | Jira Cloud instance URL for Help & Support |
| `JIRA_EMAIL` | No | Jira account email |
| `JIRA_API_TOKEN` | No | Jira API token |
| `JIRA_PROJECT_KEY` | No | Jira project key (e.g. `SUP`) |
| `POSTGRES_PASSWORD` | Docker | PostgreSQL password for the `db` Compose service |

> **Note:** Weather integration uses `OPENWEATHER_API_KEY` (OpenWeatherMap). Register at [openweathermap.org](https://openweathermap.org/api).

---

## 📡 API Endpoints

Base URL: `http://localhost:8000/api`  
Authentication: `Authorization: Bearer <accessToken>` unless noted.

### Authentication

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/auth/register` | No | Register a new user; returns JWT + profile |
| `POST` | `/auth/login` | No | Authenticate and receive JWT |
| `GET` | `/auth/me` | Yes | Get current user profile and permissions |

Default permissions on registration: `ai:chat`, `ai:embed`, `ai:search`.

### Users

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/auth/me` | Yes | Retrieve authenticated user ID, email, username, and permissions |

### Chat

| Method | Endpoint | Permission | Description |
|--------|----------|------------|-------------|
| `POST` | `/chat/` | `ai:chat` | Send a message (non-streaming) |
| `POST` | `/chat/stream` | `ai:chat` | Stream AI response via Server-Sent Events |
| `GET` | `/chat/sessions` | `ai:chat` | List all chat sessions for the user |
| `POST` | `/chat/sessions` | `ai:chat` | Create a new chat session |
| `PATCH` | `/chat/sessions/{session_id}` | `ai:chat` | Rename a session |
| `DELETE` | `/chat/sessions/{session_id}` | `ai:chat` | Delete session and cached history |
| `GET` | `/chat/history/{session_id}` | `ai:chat` | Fetch message history for a session |
| `GET` | `/chat/sessions/{session_id}/export` | `ai:chat` | Export session as plain text |

### Documents

| Method | Endpoint | Permission | Description |
|--------|----------|------------|-------------|
| `POST` | `/documents/upload` | `ai:embed` | Upload and index a PDF document |
| `GET` | `/documents/` | `ai:search` | List user's uploaded documents |
| `DELETE` | `/documents/{document_id}` | `ai:embed` | Delete document and vector embeddings |
| `POST` | `/documents/query` | `ai:search` | Query via LangGraph (RAG, FAQ, weather, support tools) |
| `GET` | `/documents/{document_id}/export` | `ai:search` | Export extracted document text |

**Query body example:**

```json
{
  "question": "What is your return policy?",
  "document_id": null,
  "session_id": "optional-session-uuid",
  "stream": false,
  "faq_mode": true,
  "weather_mode": false
}
```

### FAQ

FAQ queries use the documents query endpoint with `faq_mode: true`. The LangGraph agent routes to company policy retrieval against uploaded FAQ documents (e.g. `Company_FAQ.pdf`).

| Method | Endpoint | Permission | Description |
|--------|----------|------------|-------------|
| `POST` | `/documents/query` | `ai:search` | Ask FAQ questions (`faq_mode: true`) |

### Weather

Weather queries use the documents query endpoint with `weather_mode: true`, or natural-language detection by the agent router.

| Method | Endpoint | Permission | Description |
|--------|----------|------------|-------------|
| `POST` | `/documents/query` | `ai:search` | Get live weather (`weather_mode: true`) |

Example: `"What's the weather in Delhi?"`

### Help & Support (Jira)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/jira/create` | Yes | Create a new support issue |
| `GET` | `/jira/issues` | Yes | List issues for the configured project |
| `GET` | `/jira/{issue_key}` | Yes | Get issue details |
| `POST` | `/jira/search` | Yes | Search issues by query |
| `POST` | `/jira/assign` | Yes | Assign an issue to a user |
| `POST` | `/jira/status` | Yes | Update issue status |

### Conversations

| Method | Endpoint | Permission | Description |
|--------|----------|------------|-------------|
| `POST` | `/conversations` | `ai:chat` | Create a support conversation |
| `POST` | `/conversations/{id}/messages` | `ai:chat` | Send message → agent responds |
| `GET` | `/conversations/{id}` | `ai:chat` | Get full conversation history |
| `DELETE` | `/conversations/{id}` | `ai:chat` | Delete conversation and messages |

### Health Check

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/` | No | API health status `{ "status": "ok" }` |

---

## 📸 Screenshots

| Screen | Preview |
|--------|---------|
| Home / Dashboard | ![Home](docs/images/home.png) |
| AI Chat | ![Chat](docs/images/chat.png) |
| Login | ![Login](docs/images/login.png) |
| Swagger API Docs | ![Swagger](docs/images/swagger.png) |

> Add screenshots to `docs/images/` and they will render automatically on GitHub.

---

## ☁️ Deployment

### Docker & Docker Compose

The recommended deployment path is containerized:

1. Provision a server (e.g. AWS EC2 with Ubuntu 22.04+).
2. Install Docker and Docker Compose.
3. Clone the repository and configure `Backend/.env` with production secrets.
4. Set `POSTGRES_PASSWORD` and run `docker compose up -d --build`.
5. Verify with `docker compose ps` and curl `http://<server-ip>:8000/`.

### AWS EC2

Typical EC2 setup:

- **Instance:** `t3.medium` or larger (embedding model requires ~2 GB RAM)
- **Security groups:** Allow inbound `80`, `443`, and restrict `5432`/`6379` to private network
- **Storage:** EBS volume for Docker volumes (`postgres_data`, `redis_data`)

### Reverse Proxy & SSL

Place Nginx or Caddy in front of the containers:

```nginx
server {
    listen 443 ssl;
    server_name yourdomain.com;

    ssl_certificate     /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_buffering off;          # Required for SSE streaming
    }
}
```

Obtain certificates with [Let's Encrypt](https://letsencrypt.org/) (`certbot`) and redirect HTTP → HTTPS.

---

## 🔮 Future Enhancements

- **Token-by-token streaming** for document/RAG query responses (chat streaming already supported)
- **Voice chat** — Speech-to-text input and text-to-speech output
- **Multi-language support** — i18n for UI and multilingual model prompts
- **Analytics dashboard** — Usage metrics, query trends, and response quality
- **Admin dashboard** — User management, permission assignment, document moderation
- **Kubernetes deployment** — Helm charts for scalable container orchestration
- **CI/CD pipeline** — GitHub Actions for test, build, and deploy automation
- **Monitoring** — Prometheus metrics and Grafana dashboards for API latency and error rates

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. **Fork** the repository on GitHub.
2. **Create a branch** for your feature or fix:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes** and ensure tests pass:
   ```bash
   cd Backend && pytest
   cd Frontend && npm run lint
   ```
4. **Commit** with a clear, descriptive message.
5. **Push** to your fork and open a **Pull Request** describing what changed and why.

Please keep PRs focused, follow existing code style, and update documentation when adding new endpoints or environment variables.

---

## 📄 License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

---

## 👤 Author

| | |
|---|---|
| **Name** | Your Name |
| **GitHub** | [@your-github-username](https://github.com/your-github-username) |
| **LinkedIn** | [Your LinkedIn Profile](https://linkedin.com/in/your-profile) |
| **Email** | your.email@example.com |

---

<p align="center">
  Built with FastAPI · Next.js · LangGraph · Gemini · ChromaDB
</p>
