# Architectural Philosophy

Tattvashila Cinematic World is not designed as a traditional social platform or generic editing utility.

It is designed as a cinematic infrastructure system.

The architecture should support:

- cinematic workflows
- semantic retrieval
- archive intelligence
- narrative construction
- contemplative editing
- truth-oriented media systems
- device-adaptive cinematic environments

The system should remain modular, understandable, and scalable without becoming unnecessarily fragmented.

---

## Core Architectural Principles

### Human-Centered Systems

Technology exists to support human perception, creativity, and narrative intentionality.

AI assists workflows but does not replace authorship.

---

### Semantic Systems Over Mechanical Systems

The platform should increasingly move toward:

- semantic retrieval
- contextual organization
- emotional continuity systems
- narrative relationships
- atmospheric grouping

rather than purely manual media management.

---

### Stability Over Complexity

Architectural clarity is more important than feature density.

The system should avoid:

- unnecessary abstraction
- fragmented state ownership
- unstable workflows
- hidden system behavior

Predictability supports creative flow.

---

### Device-Adaptive Infrastructure

The architecture should support:

- mobile-native workflows
- tablet cinematic experiences
- desktop workstation capabilities

without requiring separate disconnected products.

Each environment should feel native while preserving the same cinematic philosophy.

# Architecture

**Status:** `[DRAFT]`

> This document is the canonical technical reference for the Tattvashila Cinematic
> World system. It covers the current architecture, the contracts between layers,
> and the constraints that govern future technical decisions.
> See `source-of-truth.md` Section 6 for the philosophical framing.

---

## 1. System Overview

```
┌─────────────────────────────────────────────────────────┐
│                   Frontend (React)                       │
│  Landing → Projects → Editor                            │
│  Tailwind + Shadcn | Cormorant + IBM Plex Sans          │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP / REST  (REACT_APP_BACKEND_URL)
┌────────────────────────▼────────────────────────────────┐
│                   Backend (FastAPI)                      │
│  server.py — all API routes                             │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │  pipeline/  │  │  retrieval/  │  │   services/   │  │
│  │  renderer   │  │  scene_anal  │  │  render_svc   │  │
│  │  grading    │  │  ranker      │  │  retrieval    │  │
│  │  transitions│  │  providers   │  │  provenance   │  │
│  └─────────────┘  └──────────────┘  └───────────────┘  │
│  ┌────────────┐  ┌────────────┐  ┌──────────────────┐  │
│  │ narration  │  │  storage   │  │ ambient_library  │  │
│  │ (TTS)      │  │ (obj store)│  │ (built-in presets│  │
│  └────────────┘  └────────────┘  └──────────────────┘  │
└───────────┬──────────────────┬───────────┬─────────────┘
            │                  │           │
   ┌────────▼──────┐  ┌────────▼───┐  ┌───▼───────────────┐
   │ Supabase PG   │  │  Emergent  │  │    Emergent AI     │
   │ (metadata)    │  │  Object    │  │  Claude Sonnet 4.5 │
   │ Port 6543     │  │  Storage   │  │  OpenAI TTS-1-HD   │
   │ (Transaction  │  │  (media,   │  │  (via EMERGENT_    │
   │  Pooler)      │  │   renders) │  │   LLM_KEY)         │
   └───────────────┘  └────────────┘  └────────────────────┘
```

---

## 2. Backend

### 2.1 Entry Point and Startup

| File | Role |
|------|------|
| `backend/server.py` | FastAPI app, all route definitions, CORS config |
| `backend/database.py` | Async SQLAlchemy engine (asyncpg), Supabase Postgres |
| `backend/utils/env_check.py` | Startup environment variable validation |

Startup sequence:
1. `load_dotenv(backend/.env)` — or Replit Secrets in production
2. `check_env()` — validates all required vars before any module initialises
3. Local module imports — `ambient_library`, `narration`, `repositories`, etc.
4. FastAPI app construction and route registration
5. CORS middleware: origins from `CORS_ORIGINS` env var (default: `*`)

### 2.2 Data Layer

| Component | Technology | Purpose |
|-----------|-----------|---------|
| `database.py` | SQLAlchemy async + asyncpg | Async session factory |
| `db_models.py` | SQLAlchemy ORM models | Table definitions |
| `models.py` | Pydantic models | API request/response schemas |
| `repositories.py` | Repository pattern | All DB queries, no raw SQL in routes |
| `alembic/` | Alembic | Schema migrations |

**Connection requirement:** Supabase Transaction Pooler only (port 6543).
Direct connection (5432) fails in this environment. See D001 in `decision-log.md`.

### 2.3 Key Modules

| Module | File | Depends on |
|--------|------|-----------|
| Pipeline renderer | `backend/pipeline/renderer.py` | MoviePy, FFmpeg |
| Visual grading | `backend/pipeline/grading.py` | Pillow |
| Transitions | `backend/pipeline/transitions.py` | MoviePy |
| Cinematic config | `backend/pipeline/config.py` | (none — pure config) |
| Scene analyser | `backend/retrieval/scene_analyzer.py` | `emergentintegrations`, Claude |
| Clip ranker | `backend/retrieval/ranker.py` | `emergentintegrations`, Claude |
| Stock providers | `backend/retrieval/providers.py` | httpx, Pexels API, Pixabay API |
| Retrieval trim | `backend/retrieval/trim.py` | (utility) |
| TTS narration | `backend/narration.py` | `emergentintegrations`, OpenAI TTS |
| Object storage | `backend/storage.py` | httpx, Emergent Object Storage |
| Ambient library | `backend/ambient_library.py` | FFmpeg (pre-generated MP3s) |

### 2.4 AI Integration Points

| Point | Model | Key | File |
|-------|-------|-----|------|
| Scene analysis | `claude-sonnet-4-5-20250929` | `EMERGENT_LLM_KEY` | `retrieval/scene_analyzer.py` |
| Clip ranking | `claude-sonnet-4-5-20250929` | `EMERGENT_LLM_KEY` | `retrieval/ranker.py` |
| Narration TTS | `tts-1-hd` / `tts-1` | `EMERGENT_LLM_KEY` | `narration.py` |
| Object storage init | Emergent platform | `EMERGENT_LLM_KEY` | `storage.py` |

All AI calls are routed through the `emergentintegrations` Python library.
The `EMERGENT_LLM_KEY` is the single credential for all AI and storage operations.

### 2.5 Storage Abstraction

All media I/O goes through `backend/storage.py`. No other module writes directly
to object storage. The storage module handles:

- Key initialisation and rotation on 403
- Retry with linear backoff on 5xx
- Presigned URL generation for serving

Storage URL (hardcoded in `storage.py`):
`https://integrations.emergentagent.com/objstore/api/v1/storage`

---

## 3. Frontend

### 3.1 Stack

| Component | Technology |
|-----------|-----------|
| Framework | React (CRA) |
| Styling | Tailwind CSS + Shadcn UI primitives |
| API client | Axios (`frontend/src/lib/api.js`) |
| Type system | JavaScript (no TypeScript currently) |

### 3.2 Pages

| Page | File | Route |
|------|------|-------|
| Landing | `frontend/src/pages/Landing.jsx` | `/` |
| Projects | `frontend/src/pages/Projects.jsx` | `/projects` |
| Editor | `frontend/src/pages/Editor.jsx` | `/projects/:id` |

### 3.3 Editor Panels

The editor is a multi-panel interface. All panels live in
`frontend/src/components/editor/`:

| Panel | Component | Right-panel tab |
|-------|-----------|----------------|
| Timeline | `Timeline.jsx` | (main area) |
| Media library | `MediaLibrary.jsx` | (left sidebar) |
| Narration | `NarrationPanel.jsx` | Right: Narration |
| Ambience | `AmbiencePanel.jsx` | Right: Ambience |
| Grading | `GradingPanel.jsx` | Right: Grading |
| Render | `RenderPanel.jsx` | Right: Render |
| Render progress | `RenderProgressView.jsx` | (overlay) |
| Retrieval dialog | `RetrievalDialog.jsx` | (modal) |

### 3.4 Environment Variables (Frontend)

| Variable | Purpose | Sensitive |
|----------|---------|-----------|
| `REACT_APP_BACKEND_URL` | Backend base URL | No (but deployment-specific) |
| `WDS_SOCKET_PORT` | Webpack dev server socket | No |
| `ENABLE_HEALTH_CHECK` | Enables webpack health plugin | No |

---

## 4. Infrastructure

### 4.1 Services

| Service | Purpose | Credential |
|---------|---------|-----------|
| Supabase Postgres | Project/asset/render metadata | `DATABASE_URL` |
| MongoDB Atlas | Legacy store (migration source) | `MONGO_URL` |
| Emergent Object Storage | All media files | `EMERGENT_LLM_KEY` |
| Emergent AI (Claude) | Scene analysis, clip ranking | `EMERGENT_LLM_KEY` |
| Emergent AI (OpenAI TTS) | Narration generation | `EMERGENT_LLM_KEY` |
| Pexels Videos API | Stock footage retrieval | `PEXELS_API_KEY` |
| Pixabay Videos API | Stock footage retrieval | `PIXABAY_API_KEY` |

### 4.2 Schema Management

Migrations are managed by Alembic in `backend/alembic/`.

To apply migrations:
```bash
cd backend
alembic upgrade head
```

Alembic uses a sync psycopg2 driver; it rewrites the `DATABASE_URL` scheme
from `postgresql+asyncpg://` to `postgresql+psycopg2://` internally.

### 4.3 Deployment Platform

<!-- PLACEHOLDER
     Authors: Document the current and intended deployment platform.
     Current: Replit (development). Production deployment TBD.
     Update this section when a production target is confirmed.
-->

_To be authored when production deployment is established._

---

## 5. API Reference

The backend exposes a REST API. All routes are prefixed with `/api`.

<!-- PLACEHOLDER
     Authors: This section should either be auto-generated from the FastAPI
     OpenAPI spec or manually documented for the critical routes.
     The FastAPI app at `backend/server.py` generates `/docs` (Swagger)
     and `/redoc` automatically when running.
     Decide whether to maintain this manually or reference the generated docs.
-->

Key endpoint groups:

| Group | Base path | Key operations |
|-------|-----------|---------------|
| Health | `/api/health` | GET |
| Projects | `/api/projects` | CRUD |
| Media assets | `/api/media` | Upload, list, delete |
| Renders | `/api/projects/{id}/render` | Start, status, history |
| Render status | `/api/render/{id}` | Poll, provenance |
| File serving | `/api/files/{path}` | GET (streams from object storage) |
| Ambient | `/api/ambient/library`, `/api/ambient/preview/{key}` | GET |
| Narration | `/api/narration/voices`, `/api/narration/tts` | GET, POST |
| Retrieval | `/api/retrieval/analyze`, `/api/retrieval/search`, `/api/retrieval/assemble` | POST |

---

## 6. Known Technical Debt

<!-- Maintain this section honestly. Remove entries when resolved. -->

| Item | Location | Impact | Notes |
|------|----------|--------|-------|
| MongoDB still in env | `backend/.env` | Low | Postgres migration complete; Mongo used only by migration script |
| No TypeScript in frontend | `frontend/src/` | Medium | JS-only; type errors caught only at runtime |
| `statement_cache_size=0` required | `backend/database.py` | Low | pgbouncer requirement; cannot be changed without changing pooler config |
| Model hardcoded in source | `retrieval/scene_analyzer.py`, `ranker.py` | Low | `claude-sonnet-4-5-20250929` is not configurable at runtime |

---

## Revision History

| Date | Change |
|------|--------|
| 2026-05-15 | Initial scaffold created with current architecture documented |
