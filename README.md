# SmartRecruitz

**Verified Talent Infrastructure Platform**
*by ZennialPro Private Limited*

> Single Source of Truth for Verified Talent, Interview Readiness, and Enterprise Hiring Confidence.

---

## What is SmartRecruitz?

SmartRecruitz is an enterprise-grade platform that replaces resume-centric hiring with data-backed, continuously validated candidate profiles. It sits **upstream of hiring decisions**, ensuring only verified, interview-ready talent enters enterprise hiring workflows.

**SmartRecruitz is NOT** a job portal, an ATS, or a recruiter productivity tool. It is a **Verified Talent Infrastructure** — a trust layer for enterprise hiring.

---

## How It Works: 5 AI Agents Pipeline

Candidates flow through a sequential pipeline of 5 AI agents, each powered by **Claude Sonnet** (Anthropic SDK):

```
Candidate enters chatbot
        │
        ▼
[Registration: name, email, phone]
        │
        ▼
AGENT 1: Resume Parser & Skill Normalization
   Input:  PDF/DOCX/Image resume
   Output: Structured profile JSON, normalized skills, domain classification
   AI:     Claude Sonnet (vision) — reads document directly
        │
        ▼
AGENT 2: Duplicate Detection
   Step 1: PostgreSQL pg_trgm fuzzy matching → narrows to 5-10 candidates
   Step 2: Claude semantic comparison (Bob = Robert, timeline validation)
   Output: UNIQUE → move to verified | DUPLICATE → merge/reject | UNCERTAIN → HR review
        │
        ▼
AGENT 3: ID Verification
   Input:  Aadhaar/PAN/Passport image + claimed data
   Output: OCR extraction + tampering detection + data match results
   Note:   Internal consistency check only — no government DB calls
        │
        ▼
AGENT 4: Interview Question Generation
   Input:  Candidate profile + target role
   Output: 10-15 personalized questions with expected answer points + interviewer guide
        │
        ▼
[VIDEO INTERVIEW — External service provides transcript]
        │
        ▼
AGENT 5: Interview Scoring & Readiness
   Input:  Transcript + expected answers from Agent 4
   Output: Overall score + per-question breakdown + recommendation
   ≥60%:  → TALENT_POOL    |    <60%: → INTERVIEW_FAILED (retry after 30 days)
        │
        ▼
[TALENT POOL — Verified, interviewed, ready for hiring managers]
```

**Cost:** ~$0.07 per candidate | **Time:** ~30-40 seconds total | **Claude calls:** 5 (one per agent)

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                        FRONTEND                                  │
│  ┌─────────────────────┐    ┌──────────────────────────────┐    │
│  │  Candidate Portal   │    │   Hiring Manager Portal      │    │
│  │  (Next.js)          │    │   (Next.js)                  │    │
│  │  Chatbot onboarding │    │   Dashboard + talent pool    │    │
│  └────────┬────────────┘    └──────────────┬───────────────┘    │
│           │         Shared Packages         │                    │
│           │  (ui, api-client, auth, types)  │                    │
└───────────┼─────────────────────────────────┼────────────────────┘
            │              HTTP/REST           │
┌───────────▼─────────────────────────────────▼────────────────────┐
│                        BACKEND                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │  API Layer   │→ │  Service     │→ │  Repository Layer    │   │
│  │  (FastAPI)   │  │  Layer       │  │  (SQLAlchemy async)  │   │
│  └──────────────┘  └──────┬───────┘  └──────────────────────┘   │
│                           │                                      │
│                    ┌──────▼───────┐                              │
│                    │  Agent Layer │  ← Pure AI logic             │
│                    │  (Claude)    │  ← No DB access              │
│                    └──────────────┘                              │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │  ARQ Workers │  │  Event Bus   │  │  File Storage        │   │
│  │  (Redis)     │  │  (Async)     │  │  (Local/S3)          │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
            │                                      │
   ┌────────▼────────┐                   ┌────────▼────────┐
   │   PostgreSQL    │                   │     Redis       │
   │   (JSONB +      │                   │   (Task queue + │
   │    pg_trgm)     │                   │    caching)     │
   └─────────────────┘                   └─────────────────┘
```

---

## Tech Stack

### Backend
| Component | Technology | Purpose |
|-----------|-----------|---------|
| API Framework | FastAPI (Python 3.12, async) | High-performance async REST API |
| AI Model | Claude Sonnet (Anthropic SDK) | All 5 agents — text + vision |
| Database | PostgreSQL 16 | JSONB for flexible data, pg_trgm for fuzzy search |
| ORM | SQLAlchemy (async) + Alembic | Type-safe models, schema migrations |
| Task Queue | ARQ + Redis 7 | Async background AI processing |
| Validation | Pydantic v2 | Input/output schema validation |
| File Storage | Local disk (dev) / S3 (prod) | Resume and ID document storage |
| Observability | structlog + Prometheus | Structured logging, metrics |
| Containerization | Docker + Docker Compose | Postgres, Redis, API, Worker |

### Frontend
| Component | Technology | Purpose |
|-----------|-----------|---------|
| Framework | Next.js 15 (App Router) + TypeScript | SSR, routing, middleware |
| UI Library | shadcn/ui + Radix UI + Tailwind CSS 4 | Accessible, customizable components |
| State | Zustand (client) + TanStack Query v5 (server) | Minimal boilerplate, smart caching/polling |
| Forms | React Hook Form + Zod | Performant forms with type-safe validation |
| Charts | Recharts | Dashboard KPIs, skill radars, score breakdowns |
| Auth | NextAuth.js v5 | SSO, magic links, session management |
| Monorepo | Turborepo + pnpm | Parallel builds, caching, shared packages |
| Testing | Vitest + Playwright | Unit/integration + E2E |

---

## Project Structure

```
smartrecruitz/
├── backend/                    # FastAPI Python backend
│   ├── app/                    # Application code
│   │   ├── api/v1/             # REST endpoints
│   │   ├── agents/             # 5 AI agents (pure Claude logic)
│   │   ├── services/           # Business logic orchestration
│   │   ├── repositories/       # Data access layer
│   │   ├── models/             # SQLAlchemy models (20+ tables)
│   │   ├── schemas/            # Pydantic request/response models
│   │   ├── core/               # Security, events, middleware, observability
│   │   ├── workers/            # ARQ background task handlers
│   │   └── config/             # Settings, constants, feature flags
│   ├── tests/                  # Unit, integration, E2E, load tests
│   ├── seeds/                  # Skill taxonomy, roles, demo data
│   ├── docker/                 # Dockerfiles, compose, nginx
│   └── README.md               # Backend architecture document
├── frontend/                   # Next.js TypeScript frontend
│   ├── apps/
│   │   ├── candidate-portal/   # Chatbot onboarding flow (7 steps)
│   │   └── hiring-portal/      # Hiring manager dashboard
│   ├── packages/               # Shared: ui, api-client, auth, types
│   ├── tooling/                # ESLint, TypeScript, Tailwind configs
│   └── README.md               # Frontend architecture document
└── README.md                   # This file
```

---

## Candidate Status Flow

```
PENDING (staging)
    │
    ├──→ DUPLICATE_REVIEW ──→ REJECTED
    │                    └──→ HR resolves ──→ continues
    │
    ▼ (unique)
VERIFIED (main)
    │
    ▼
IDENTITY_VERIFIED ──── or ──── VERIFICATION_FAILED
    │
    ▼
INTERVIEW_READY ────── or ──── INTERVIEW_FAILED (retry after 30 days)
    │
    ▼
TALENT_POOL
```

---

## Database Schema (11 core tables + enterprise tables)

### Core Pipeline Tables
| Table | Purpose |
|-------|---------|
| `candidates_staging` | Temporary raw data from Agent 1 |
| `candidates_main` | Verified candidates with normalized relations |
| `candidate_skills` | Candidate ↔ skill_taxonomy mapping with proficiency |
| `candidate_experiences` | Work history with domain classification |
| `candidate_educations` | Education records |
| `skill_taxonomy` | Master skill list with aliases and hierarchy |
| `verifications` | Agent 3 ID verification results |
| `interviews` | Interview records with scores and recommendations |
| `interview_questions` | Generated questions with expected answers |
| `uploaded_documents` | Resume and ID document file metadata |
| `background_tasks` | Async task tracking (QUEUED → PROCESSING → COMPLETED) |

### Enterprise Tables
| Table | Purpose |
|-------|---------|
| `audit_logs` | Immutable, append-only activity log |
| `tenants` | Organization registry (future multi-tenant) |
| `users` | Platform users (admins, HR reviewers) |
| `roles` / `permissions` | RBAC system |
| `api_keys` | Integration authentication |
| `webhook_subscriptions` | Outbound event subscriptions |
| `data_consents` | GDPR consent tracking |

---

## API Endpoints

### Candidate Registration
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/candidates/register` | Register new candidate |
| `GET` | `/api/v1/candidates/staging` | List staging candidates |
| `GET` | `/api/v1/candidates/staging/{ref}` | Get staging candidate detail |
| `GET` | `/api/v1/candidates` | List verified candidates |
| `GET` | `/api/v1/candidates/{ref}` | Get full candidate profile |

### AI Agent Endpoints (async — returns `task_id`)
| Method | Path | Agent |
|--------|------|-------|
| `POST` | `/api/v1/agent1/parse-resume` | Resume Parser |
| `POST` | `/api/v1/agent2/check-duplicate` | Duplicate Detection |
| `POST` | `/api/v1/agent2/resolve` | HR Duplicate Resolution |
| `POST` | `/api/v1/agent3/verify-identity` | ID Verification |
| `POST` | `/api/v1/agent4/generate-questions` | Question Generation |
| `POST` | `/api/v1/agent5/score-interview` | Interview Scoring |

### System
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/tasks/{task_id}` | Poll task status + result |
| `GET` | `/api/v1/skills/taxonomy` | Search skill taxonomy |
| `GET` | `/health/ready` | Readiness probe |

---

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.12+
- Node.js 20+ & pnpm
- Anthropic API key

### Backend
```bash
cd backend
cp .env.example .env                    # Add your ANTHROPIC_API_KEY
docker compose -f docker/docker-compose.yml up -d   # Start Postgres + Redis
make migrate                            # Run database migrations
make seed                               # Seed skill taxonomy + roles
make dev                                # Start API server + worker
```

### Frontend
```bash
cd frontend
pnpm install                            # Install all dependencies
pnpm dev                                # Start both portals in parallel
```

- Candidate Portal: `http://localhost:3000`
- Hiring Manager Portal: `http://localhost:3001`
- API Docs: `http://localhost:8000/docs`

---

## Design Principles

1. **No LangChain. No LangGraph.** All agents are single-call to Claude — no chaining, no memory framework needed.
2. **4-Layer Separation:** API (thin HTTP) → Service (business logic) → Repository (data access) → Agent (pure AI). No layer bypasses another.
3. **Async Everything:** All AI calls run as background tasks via ARQ. Frontend polls for results.
4. **Enterprise-Ready Schema:** Multi-tenant columns, audit trails, RBAC, and GDPR consent designed in from Day 1.
5. **Trust Over Volume:** The platform prioritizes verified, high-quality talent profiles over processing speed.

---

## Documentation

| Document | Location |
|----------|----------|
| Backend Architecture | [`backend/README.md`](backend/README.md) |
| Frontend Architecture | [`frontend/README.md`](frontend/README.md) |
| API Reference | Auto-generated at `/docs` (Swagger UI) |
| PRD | `../PRD_ZennialPro_SmartRecruitZ_Chromezy_2026 - 2027.pdf` |
| Technical Design | `../SmartRecruitz_Technical_Design_Document.md` |

---

## License

Proprietary - ZennialPro Private Limited. All rights reserved.
