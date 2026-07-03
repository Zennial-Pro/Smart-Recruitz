# SmartRecruitz Backend

**Enterprise-Grade FastAPI Backend for Verified Talent Infrastructure**

---

## Table of Contents

1. [Tech Stack](#tech-stack)
2. [Architecture Overview](#architecture-overview)
3. [Folder Structure](#folder-structure)
4. [4-Layer Architecture](#4-layer-architecture)
5. [Database Design](#database-design)
6. [AI Agents](#ai-agents)
7. [Background Processing](#background-processing)
8. [API Endpoints](#api-endpoints)
9. [Authentication & Security](#authentication--security)
10. [Event System](#event-system)
11. [Error Handling](#error-handling)
12. [Observability](#observability)
13. [Configuration](#configuration)
14. [Testing Strategy](#testing-strategy)
15. [Docker & Deployment](#docker--deployment)
16. [Development Guide](#development-guide)

---

## Tech Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **API Framework** | FastAPI | 0.115+ | Async REST API with auto-generated OpenAPI docs |
| **Language** | Python | 3.12 | Async/await, type hints, pattern matching |
| **AI Model** | Claude Sonnet | via Anthropic SDK | All 5 agents — text + document/image analysis |
| **Database** | PostgreSQL | 16 | JSONB for flexible data, pg_trgm for fuzzy search |
| **ORM** | SQLAlchemy | 2.0+ (async) | Type-safe models, relationship management |
| **Migrations** | Alembic | latest | Database schema versioning |
| **Task Queue** | ARQ | latest | Async background processing for AI agent calls |
| **Cache/Queue** | Redis | 7 | Task queue backend, rate limiting, caching |
| **Validation** | Pydantic | v2 | Input/output schema validation with JSON Schema |
| **File Storage** | Local / S3 | - | Resume and ID document storage |
| **HTTP Client** | httpx | latest | Async outbound HTTP calls (webhooks, ATS push) |
| **Logging** | structlog | latest | Structured JSON logging |
| **Metrics** | prometheus-client | latest | Application metrics |
| **Containerization** | Docker + Compose | latest | Development and production environments |
| **Linting** | Ruff | latest | Fast Python linter + formatter |
| **Type Checking** | mypy | latest | Static type analysis (strict mode) |
| **Testing** | pytest + pytest-asyncio | latest | Async test support |

**Key decision: No LangChain. No LangGraph.** All agents are single-call to Claude — no chaining, no memory framework needed. This keeps the codebase simple, debuggable, and cost-efficient (~$0.07 per candidate across all 5 agents).

---

## Architecture Overview

### 4-Layer Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  API Layer (app/api/v1/)                                     │
│  Thin HTTP handlers. Receives requests, validates input,     │
│  calls service, returns response. ZERO business logic.       │
└──────────────────────┬───────────────────────────────────────┘
                       │ calls
┌──────────────────────▼───────────────────────────────────────┐
│  Service Layer (app/services/)                               │
│  Business logic orchestration. DB operations via repos,      │
│  triggers agents, manages state transitions, emits events.   │
└──────────┬───────────────────────────────┬───────────────────┘
           │ uses                          │ calls
┌──────────▼──────────┐         ┌─────────▼───────────────────┐
│  Repository Layer   │         │  Agent Layer (app/agents/)   │
│  (app/repositories/)│         │  Pure AI logic. Builds       │
│  Data access only.  │         │  prompts, calls Claude,      │
│  CRUD + queries.    │         │  parses responses.           │
│  Tenant-scoped.     │         │  NO DB access. Testable      │
│  Soft-delete aware. │         │  by mocking Claude.          │
└─────────────────────┘         └──────────────────────────────┘
```

**Rules:**
- Dependencies flow **downward only**: API → Service → Repository/Agent
- No layer may bypass the one beneath it
- Agents have **zero** database access — they receive input and return output
- Repositories have **zero** business logic — they execute queries
- Services coordinate everything through the **Unit of Work** pattern

### Background Processing Flow

```
Frontend POST /agent1/parse-resume
    │
    ▼
API handler creates background_task record (status: QUEUED)
    │
    ▼
Returns { task_id } to frontend immediately (< 100ms)
    │
    ▼
ARQ worker picks up the job from Redis queue
    │
    ▼
Worker calls Service → Service calls Agent → Agent calls Claude
    │
    ▼
Worker saves result to DB, updates background_task (status: COMPLETED)
    │
    ▼
Frontend polls GET /tasks/{task_id} → receives result
```

---

## Folder Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                              # FastAPI application factory
│   ├── asgi.py                              # ASGI entrypoint for Uvicorn
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py                      # Pydantic BaseSettings (env-driven)
│   │   ├── constants.py                     # Status enums, business constants, ref prefixes
│   │   └── feature_flags.py                 # Runtime feature flag registry
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── security/
│   │   │   ├── __init__.py
│   │   │   ├── authentication.py            # JWT decode/verify, OAuth2 password flow
│   │   │   ├── authorization.py             # RBAC permission checker dependency
│   │   │   ├── rbac_models.py               # Role, Permission dataclass definitions
│   │   │   ├── api_key_manager.py           # API key generation, validation, rotation
│   │   │   ├── encryption.py                # AES-256-GCM field-level encryption
│   │   │   ├── hashing.py                   # Argon2id for passwords, SHA-256 for API keys
│   │   │   ├── cors.py                      # CORS origin configuration
│   │   │   └── rate_limiter.py              # Redis sliding window rate limiter
│   │   │
│   │   ├── events/
│   │   │   ├── __init__.py
│   │   │   ├── event_bus.py                 # In-process async pub/sub event bus
│   │   │   ├── event_types.py               # Typed domain event classes
│   │   │   ├── handlers/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── audit_handler.py         # Writes to immutable audit_logs table
│   │   │   │   ├── notification_handler.py  # Email/push notifications
│   │   │   │   ├── webhook_dispatcher.py    # Enqueues outbound webhook delivery
│   │   │   │   └── integration_handler.py   # ATS/LMS event relay
│   │   │   └── decorators.py               # @emit_event convenience decorator
│   │   │
│   │   ├── exceptions/
│   │   │   ├── __init__.py
│   │   │   ├── base.py                      # SmartRecruitzError base class
│   │   │   ├── domain.py                    # CandidateNotFoundError, DuplicateCandidateError, etc.
│   │   │   ├── agent.py                     # AgentTimeoutError, AgentResponseParseError
│   │   │   ├── auth.py                      # AuthenticationFailedError, InsufficientPermissionsError
│   │   │   ├── validation.py                # SchemaValidationError, FileValidationError
│   │   │   └── error_codes.py               # Enum: SR-AUTH-001, SR-CAND-001, SR-AGENT-001, etc.
│   │   │
│   │   ├── middleware/
│   │   │   ├── __init__.py
│   │   │   ├── request_id.py               # Injects X-Request-ID for correlation
│   │   │   ├── tenant_context.py           # Sets tenant_id in contextvars from JWT
│   │   │   ├── rate_limit.py               # Per-endpoint rate limiting via Redis
│   │   │   ├── audit_trail.py              # Logs mutating requests (POST/PUT/DELETE)
│   │   │   ├── error_handler.py            # Global exception → HTTP response mapping
│   │   │   ├── timing.py                   # Request duration metrics
│   │   │   └── security_headers.py         # HSTS, X-Content-Type-Options, CSP
│   │   │
│   │   ├── observability/
│   │   │   ├── __init__.py
│   │   │   ├── logging.py                  # structlog config: JSON in prod, pretty in dev
│   │   │   ├── metrics.py                  # Prometheus counters/histograms
│   │   │   ├── tracing.py                  # OpenTelemetry span management
│   │   │   └── health.py                   # GET /health/live and /health/ready
│   │   │
│   │   ├── clients/
│   │   │   ├── __init__.py
│   │   │   ├── anthropic_client.py         # Claude SDK wrapper: retry, timeout, token tracking
│   │   │   ├── s3_client.py                # Boto3 async wrapper for S3
│   │   │   ├── redis_client.py             # Redis connection pool manager
│   │   │   └── http_client.py              # httpx AsyncClient for outbound calls
│   │   │
│   │   ├── storage/
│   │   │   ├── __init__.py
│   │   │   ├── base.py                     # Abstract FileStorage interface
│   │   │   ├── local_storage.py            # Dev: writes to ./uploads/
│   │   │   └── s3_storage.py               # Prod: S3 with presigned URLs
│   │   │
│   │   └── pagination.py                   # Cursor-based and offset pagination utilities
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── session.py                       # async_sessionmaker, create_async_engine
│   │   ├── base.py                          # DeclarativeBase with common config
│   │   ├── mixins.py                        # TimestampMixin, SoftDeleteMixin, AuditMixin
│   │   ├── unit_of_work.py                  # UnitOfWork: wraps session + all repos
│   │   └── migrations/
│   │       ├── env.py                       # Alembic async environment
│   │       ├── script.py.mako               # Migration template
│   │       └── versions/                    # Auto-generated migration files
│   │
│   ├── models/
│   │   ├── __init__.py                      # Re-exports all models for Alembic
│   │   ├── candidate_staging.py             # Temporary parsed resume data
│   │   ├── candidate_main.py                # Verified candidate profiles
│   │   ├── candidate_skill.py               # Candidate ↔ skill_taxonomy FK
│   │   ├── candidate_experience.py          # Work history entries
│   │   ├── candidate_education.py           # Education records
│   │   ├── skill_taxonomy.py                # Master skill list with aliases
│   │   ├── verification.py                  # Agent 3 ID verification results
│   │   ├── interview.py                     # Interview sessions with scores
│   │   ├── interview_question.py            # Generated questions + scoring
│   │   ├── uploaded_document.py             # File metadata (resume, ID docs)
│   │   ├── background_task.py               # Async task tracking
│   │   ├── audit_log.py                     # Immutable append-only log
│   │   ├── tenant.py                        # Organization registry
│   │   ├── user.py                          # Platform users
│   │   ├── role.py                          # RBAC roles
│   │   ├── permission.py                    # RBAC permissions
│   │   ├── api_key.py                       # API key records
│   │   ├── webhook_subscription.py          # Outbound webhook configuration
│   │   ├── webhook_delivery_log.py          # Webhook delivery attempts
│   │   ├── lms_event.py                     # Inbound LMS event staging
│   │   └── data_consent.py                  # GDPR consent tracking
│   │
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── base.py                          # BaseRepository[T]: async CRUD, soft delete
│   │   ├── candidate_staging_repo.py        # Staging-specific queries
│   │   ├── candidate_main_repo.py           # Includes pg_trgm fuzzy_search()
│   │   ├── candidate_skill_repo.py
│   │   ├── candidate_experience_repo.py
│   │   ├── candidate_education_repo.py
│   │   ├── skill_taxonomy_repo.py           # Skill search with alias matching
│   │   ├── verification_repo.py
│   │   ├── interview_repo.py
│   │   ├── interview_question_repo.py
│   │   ├── document_repo.py
│   │   ├── task_repo.py
│   │   ├── audit_log_repo.py               # Append-only: create() and list() only
│   │   ├── tenant_repo.py
│   │   ├── user_repo.py
│   │   └── webhook_repo.py
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── base.py                          # BaseSchema: orjson config, camelCase aliases
│   │   ├── requests/
│   │   │   ├── __init__.py
│   │   │   ├── candidate.py                 # CandidateRegisterRequest
│   │   │   ├── agent1.py                    # ResumeParseRequest
│   │   │   ├── agent2.py                    # DuplicateCheckRequest, DuplicateResolveRequest
│   │   │   ├── agent3.py                    # IdentityVerifyRequest
│   │   │   ├── agent4.py                    # QuestionGenerateRequest
│   │   │   ├── agent5.py                    # InterviewScoreRequest
│   │   │   ├── taxonomy.py                  # SkillCreateRequest
│   │   │   └── auth.py                      # LoginRequest, TokenRefreshRequest
│   │   ├── responses/
│   │   │   ├── __init__.py
│   │   │   ├── candidate.py                 # CandidateStagingResponse, CandidateMainResponse
│   │   │   ├── task.py                      # TaskStatusResponse
│   │   │   ├── agent_results.py             # Typed response per agent
│   │   │   ├── taxonomy.py                  # SkillTaxonomyResponse
│   │   │   ├── auth.py                      # TokenResponse
│   │   │   ├── error.py                     # StandardErrorResponse
│   │   │   └── pagination.py                # PaginatedResponse[T] generic
│   │   └── internal/
│   │       ├── __init__.py
│   │       ├── agent1_io.py                 # ResumeParserInput/Output
│   │       ├── agent2_io.py                 # DuplicateDetectionInput/Output
│   │       ├── agent3_io.py                 # IDVerificationInput/Output
│   │       ├── agent4_io.py                 # QuestionGenInput/Output
│   │       └── agent5_io.py                 # InterviewScoreInput/Output
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── candidate_service.py             # Registration, staging/main lifecycle
│   │   ├── resume_parse_service.py          # Orchestrates Agent 1 pipeline
│   │   ├── duplicate_service.py             # Orchestrates Agent 2 (DB query + AI call)
│   │   ├── verification_service.py          # Orchestrates Agent 3
│   │   ├── question_gen_service.py          # Orchestrates Agent 4
│   │   ├── interview_score_service.py       # Orchestrates Agent 5
│   │   ├── task_service.py                  # Background task lifecycle management
│   │   ├── taxonomy_service.py              # Skill taxonomy CRUD + search
│   │   ├── document_service.py              # File upload/download orchestration
│   │   ├── auth_service.py                  # Login, token issuance, API key management
│   │   ├── tenant_service.py                # Tenant provisioning
│   │   ├── webhook_service.py               # Webhook subscription management
│   │   ├── lms_ingestion_service.py         # LMS event processing
│   │   ├── consent_service.py               # GDPR consent management
│   │   └── ref_generator.py                 # Business ref generation (SR-2024-00123)
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py                          # BaseAgent ABC: prompt load, Claude call, parse
│   │   ├── agent1_resume_parser.py          # Vision: PDF/image → structured profile JSON
│   │   ├── agent2_duplicate.py              # Text: semantic candidate comparison
│   │   ├── agent3_verification.py           # Vision: ID OCR + tampering detection
│   │   ├── agent4_question_gen.py           # Text: personalized interview questions
│   │   ├── agent5_interview_score.py        # Text: transcript evaluation + scoring
│   │   ├── prompts/
│   │   │   ├── agent1_system.txt            # System prompt for resume parser
│   │   │   ├── agent1_user.txt.jinja        # User prompt template with candidate context
│   │   │   ├── agent2_system.txt
│   │   │   ├── agent2_user.txt.jinja
│   │   │   ├── agent3_system.txt
│   │   │   ├── agent3_user.txt.jinja
│   │   │   ├── agent4_system.txt
│   │   │   ├── agent4_user.txt.jinja
│   │   │   ├── agent5_system.txt
│   │   │   └── agent5_user.txt.jinja
│   │   └── validators/
│   │       ├── __init__.py
│   │       ├── agent1_validator.py          # Validates resume parse output schema
│   │       ├── agent2_validator.py
│   │       ├── agent3_validator.py
│   │       ├── agent4_validator.py
│   │       └── agent5_validator.py
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py                          # Dependency injection: get_db, get_current_user, etc.
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py                    # Aggregates all v1 sub-routers
│   │       ├── candidates.py                # POST /register, GET /staging, GET /candidates
│   │       ├── agent1.py                    # POST /agent1/parse-resume
│   │       ├── agent2.py                    # POST /agent2/check-duplicate, /resolve
│   │       ├── agent3.py                    # POST /agent3/verify-identity
│   │       ├── agent4.py                    # POST /agent4/generate-questions
│   │       ├── agent5.py                    # POST /agent5/score-interview
│   │       ├── tasks.py                     # GET /tasks/{task_id}
│   │       ├── taxonomy.py                  # GET/POST /skills/taxonomy
│   │       ├── auth.py                      # POST /auth/login, /refresh, /logout
│   │       ├── webhooks.py                  # Inbound LMS webhook receiver
│   │       ├── admin.py                     # Tenant/user management
│   │       └── health.py                    # /health/live, /health/ready
│   │
│   ├── workers/
│   │   ├── __init__.py
│   │   ├── worker_main.py                   # ARQ worker bootstrap + settings
│   │   ├── task_registry.py                 # Maps task_type → handler function
│   │   ├── handlers/
│   │   │   ├── __init__.py
│   │   │   ├── agent1_handler.py            # resume_parse_task()
│   │   │   ├── agent2_handler.py            # duplicate_check_task()
│   │   │   ├── agent3_handler.py            # identity_verify_task()
│   │   │   ├── agent4_handler.py            # question_generate_task()
│   │   │   ├── agent5_handler.py            # interview_score_task()
│   │   │   ├── webhook_delivery_handler.py  # Outbound webhook with retry
│   │   │   └── lms_processing_handler.py    # LMS event enrichment
│   │   └── callbacks.py                     # on_startup, on_shutdown, on_job_error
│   │
│   └── utils/
│       ├── __init__.py
│       ├── datetime_utils.py                # UTC-aware helpers
│       ├── json_utils.py                    # ORJSON serialization
│       ├── hash_utils.py                    # Question hash generation (SHA-256)
│       └── validators.py                    # Email, phone, ref format validators
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                          # Shared fixtures: test DB, client, mock Claude
│   ├── factories/
│   │   ├── __init__.py
│   │   ├── candidate_factory.py             # CandidateStaging/Main factories
│   │   ├── user_factory.py
│   │   └── taxonomy_factory.py
│   ├── fixtures/
│   │   ├── sample_resume.pdf
│   │   ├── sample_aadhaar.png
│   │   ├── sample_transcript.txt
│   │   ├── agent1_response.json             # Canned Claude response
│   │   ├── agent2_response.json
│   │   ├── agent3_response.json
│   │   ├── agent4_response.json
│   │   └── agent5_response.json
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── agents/                          # Test each agent with mocked Claude
│   │   ├── services/                        # Test business logic with mocked repos
│   │   ├── repositories/                    # Test queries against real test DB
│   │   └── security/                        # Test auth, RBAC, encryption
│   ├── integration/
│   │   ├── __init__.py
│   │   ├── test_candidate_flow.py           # Registration through staging
│   │   ├── test_agent_pipeline.py           # Agent 1-5 with mocked Claude
│   │   └── test_rbac_enforcement.py
│   ├── e2e/
│   │   ├── __init__.py
│   │   └── test_full_candidate_pipeline.py  # Register → Agent 1-5 → Talent Pool
│   └── load/
│       ├── locustfile.py
│       └── scenarios/
│           ├── candidate_registration.py
│           └── agent_pipeline.py
│
├── seeds/
│   ├── __init__.py
│   ├── seed_runner.py                       # CLI entry point
│   ├── skill_taxonomy_seed.json             # 500+ normalized skills with aliases
│   ├── roles_permissions_seed.json          # Default RBAC roles + permissions
│   └── demo_tenant_seed.json               # Dev/demo tenant data
│
├── scripts/
│   ├── create_migration.sh                  # alembic revision --autogenerate wrapper
│   ├── run_migrations.sh                    # alembic upgrade head
│   └── seed_db.sh                           # Run all seeds
│
├── docker/
│   ├── Dockerfile                           # Multi-stage: builder → runtime
│   ├── Dockerfile.worker                    # Same base, different CMD
│   ├── docker-compose.yml                   # Dev: postgres + redis + api + worker
│   ├── docker-compose.prod.yml              # Prod overrides
│   ├── docker-compose.test.yml              # Ephemeral test DB + Redis
│   └── nginx/
│       └── nginx.conf                       # Reverse proxy, SSL termination
│
├── docs/
│   └── adr/                                 # Architecture Decision Records
│       ├── 001-async-everywhere.md
│       ├── 002-no-langchain.md
│       ├── 003-event-bus-in-process.md
│       └── 004-repository-pattern.md
│
├── .env.example                             # Template with ALL env vars documented
├── .env.test                                # Test env (committed, no secrets)
├── pyproject.toml                           # Dependencies + tool configs (ruff, mypy, pytest)
├── alembic.ini                              # Alembic configuration
├── Makefile                                 # dev, test, lint, migrate, seed, docker-up
└── README.md                                # This file
```

---

## 4-Layer Architecture

### Layer 1: API Layer (`app/api/`)

**Responsibility:** HTTP request/response handling. Zero business logic.

Every route handler does exactly three things:
1. Accept and validate the HTTP request (Pydantic does this automatically)
2. Call the appropriate service method
3. Return the formatted response

```python
# Pattern for every route handler
@router.post("/register", response_model=CandidateRegistrationResponse, status_code=201)
async def register_candidate(
    request: CandidateRegisterRequest,
    service: CandidateService = Depends(get_candidate_service),
    current_user: User = Depends(get_current_user),
) -> CandidateRegistrationResponse:
    result = await service.register(request)
    return CandidateRegistrationResponse.from_domain(result)
```

Agent endpoints follow the async pattern — return `task_id` immediately:

```python
@router.post("/parse-resume", response_model=TaskCreatedResponse, status_code=202)
async def parse_resume(
    candidate_ref: str = Form(...),
    file: UploadFile = File(...),
    service: ResumeParseService = Depends(get_resume_parse_service),
) -> TaskCreatedResponse:
    task_id = await service.enqueue(candidate_ref, file)
    return TaskCreatedResponse(task_id=task_id)
```

### Layer 2: Service Layer (`app/services/`)

**Responsibility:** Business logic orchestration. This is the brain of the application.

Services coordinate between repositories and agents:
- Enforce business rules (e.g., candidate must be IDENTITY_VERIFIED before Agent 4)
- Manage state transitions (staging → main)
- Own transaction boundaries (via Unit of Work)
- Emit domain events (after successful operations)

**Example: Duplicate Detection Service orchestration**

```
DuplicateService.check(candidate_ref):
  1. staging_repo.get_by_ref(ref)                    # Fetch staging record
  2. main_repo.fuzzy_search(name, email, phone)      # DB-level fuzzy matching (free)
  3. agent2.analyze(new_candidate, potential_matches) # One Claude API call
  4. IF UNIQUE:
       main_repo.create_from_staging(...)             # Insert into candidates_main
       staging_repo.update_status(COMPLETED)          # Mark staging as done
       event_bus.emit(CandidateVerifiedEvent)
     IF DUPLICATE:
       staging_repo.update_status(DUPLICATE_REVIEW)
       event_bus.emit(DuplicateDetectedEvent)
     IF UNCERTAIN:
       staging_repo.update_status(AWAITING_HR_REVIEW)
       event_bus.emit(HRReviewRequiredEvent)
```

### Layer 3: Repository Layer (`app/repositories/`)

**Responsibility:** Data access abstraction. All database operations encapsulated here.

The `BaseRepository[T]` provides:
- `get_by_id(id)` — with soft delete filter
- `list(filters, pagination)` — with cursor/offset pagination
- `create(data)` — with timestamp population
- `update(id, data)` — with updated_at population
- `soft_delete(id)` — sets `deleted_at`
- `hard_delete(id)` — for GDPR data erasure

Specialized repositories extend the base:

```python
class CandidateMainRepo(BaseRepository[CandidateMain]):
    async def fuzzy_search(self, name: str, email: str, phone: str) -> list[CandidateMain]:
        """Uses pg_trgm similarity for fuzzy name matching."""
        stmt = (
            select(self._model)
            .where(
                or_(
                    self._model.email == email,
                    self._model.phone == phone,
                    func.similarity(self._model.full_name, name) > 0.3,
                )
            )
            .order_by(func.similarity(self._model.full_name, name).desc())
            .limit(10)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
```

### Layer 4: Agent Layer (`app/agents/`)

**Responsibility:** Pure AI interaction. No database access. No business rules.

Each agent inherits from `BaseAgent`:

```python
class BaseAgent(ABC):
    def __init__(self, client: AnthropicClient, prompt_dir: Path):
        self._client = client
        self._prompt_dir = prompt_dir

    @abstractmethod
    def _build_messages(self, input_data: BaseModel) -> list[dict]: ...

    @abstractmethod
    def _parse_response(self, raw: str) -> BaseModel: ...

    async def execute(self, input_data: BaseModel) -> BaseModel:
        system_prompt = self._load_prompt("system.txt")
        messages = self._build_messages(input_data)
        raw_response = await self._client.create_message(
            system=system_prompt,
            messages=messages,
            model="claude-sonnet-4-20250514",
        )
        return self._parse_response(raw_response.content[0].text)
```

- **Vision agents** (1, 3): Pass base64-encoded PDF/image in messages
- **Text agents** (2, 4, 5): Pass structured JSON in user message
- **Prompt templates**: System prompts as `.txt`, user prompts as Jinja2 `.txt.jinja`

### Unit of Work Pattern

```python
class UnitOfWork:
    def __init__(self, session_factory: async_sessionmaker):
        self._session_factory = session_factory

    async def __aenter__(self):
        self._session = self._session_factory()
        self.candidates_staging = CandidateStagingRepo(self._session)
        self.candidates_main = CandidateMainRepo(self._session)
        self.skills = SkillTaxonomyRepo(self._session)
        # ... all repositories
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self._session.rollback()
        await self._session.close()

    async def commit(self):
        await self._session.commit()
```

---

## Database Design

### Table Overview

```
candidates_staging (temporary, raw from Agent 1)
        │
        │ Agent 2 moves unique candidates
        ▼
candidates_main (verified candidates)
   ├── candidate_skills (FK → skill_taxonomy)
   ├── candidate_experiences
   ├── candidate_educations
   ├── verifications (Agent 3 results)
   └── interviews → interview_questions (Agent 4 + Agent 5)

skill_taxonomy (master skill list)
uploaded_documents (resumes, ID docs)
background_tasks (async processing tracker)
audit_logs (immutable activity log)
```

### Core Tables

#### candidates_staging
Temporary storage. Raw parsed data as JSONB. Deleted/moved after duplicate check.

| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | gen_random_uuid() |
| candidate_ref | VARCHAR(50) | Business key: "SR-2024-00123" |
| status | VARCHAR(30) | PENDING / DUPLICATE_REVIEW / AWAITING_HR_REVIEW / COMPLETED / REJECTED |
| full_name | VARCHAR(255) | |
| email | VARCHAR(255) | Indexed |
| phone | VARCHAR(50) | Indexed |
| current_title | VARCHAR(255) | |
| raw_resume_data | JSONB | Full Agent 1 output |
| skills_normalized | JSONB | Array of normalized skills |
| experience | JSONB | Array of experience entries |
| education | JSONB | Array of education entries |
| certifications | JSONB | |
| projects | JSONB | |
| languages | JSONB | |
| total_experience_years | FLOAT | |
| primary_domain | VARCHAR(100) | FinTech, Healthcare, E-Commerce, etc. |
| domain_experience | JSONB | Domain-wise breakdown |
| parse_confidence | FLOAT | AI confidence 0-1 |
| duplicate_pre_check | JSONB | Quick check result from Agent 1 |
| resume_document_id | UUID (FK) | → uploaded_documents |
| created_at | TIMESTAMP | auto |
| updated_at | TIMESTAMP | auto |

#### candidates_main
Verified candidates with normalized child tables.

| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| candidate_ref | VARCHAR(50) | Unique business key |
| status | VARCHAR(30) | VERIFIED / IDENTITY_VERIFIED / INTERVIEW_READY / TALENT_POOL / INTERVIEW_FAILED / CLOSED |
| full_name | VARCHAR(255) | GIN trigram index for fuzzy search |
| email | VARCHAR(255) | Unique |
| phone | VARCHAR(50) | Unique |
| current_title | VARCHAR(255) | |
| total_experience_years | FLOAT | |
| primary_domain | VARCHAR(100) | Indexed |
| location | VARCHAR(255) | |
| target_role | VARCHAR(255) | |
| readiness_score | FLOAT | Set by Agent 5 |
| verification_status | VARCHAR(30) | PENDING / VERIFIED / FAILED |
| talent_pool_entry_date | TIMESTAMP | |
| raw_profile_data | JSONB | Complete parsed profile |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

#### skill_taxonomy
Master skill list. All candidate skills map to this.

| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| standard_name | VARCHAR(255) | Unique: "JavaScript" |
| category | VARCHAR(100) | Programming Language, Framework, Cloud, etc. |
| aliases | JSONB | ["JS", "ECMAScript", "Javascript"] — GIN indexed |
| parent_skill_id | UUID (FK) | Self-referential hierarchy |

#### background_tasks

| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| task_type | VARCHAR(50) | AGENT1_RESUME_PARSE / AGENT2_DUPLICATE / etc. |
| reference_id | VARCHAR(50) | candidate_ref or interview_ref |
| status | VARCHAR(20) | QUEUED / PROCESSING / COMPLETED / FAILED |
| result | JSONB | Agent output when completed |
| error_message | TEXT | If failed |
| created_at | TIMESTAMP | |
| started_at | TIMESTAMP | |
| completed_at | TIMESTAMP | |

### Indexing Strategy

| Table | Index | Type |
|-------|-------|------|
| candidates_staging | `(email)`, `(phone)`, `(status)` | B-tree |
| candidates_main | `(full_name)` | GIN trigram |
| candidates_main | `(email)` UNIQUE, `(phone)` UNIQUE | B-tree |
| candidates_main | `(status)`, `(primary_domain)` | B-tree |
| candidate_skills | `(candidate_id, skill_id)` UNIQUE | B-tree |
| skill_taxonomy | `(standard_name)` UNIQUE | B-tree |
| skill_taxonomy | `(aliases)` | GIN |
| interview_questions | `(question_hash)` | B-tree |
| background_tasks | `(status)`, `(reference_id)` | B-tree |
| audit_logs | `(created_at)` | B-tree (partitioned monthly) |

---

## AI Agents

### Agent Summary

| Agent | Model | Type | Input | Output | Cost | Time |
|-------|-------|------|-------|--------|------|------|
| 1. Resume Parser | Claude Sonnet (vision) | PDF/Image | Resume file | Structured profile JSON | ~$0.02 | 5-10s |
| 2. Duplicate Detection | Claude Sonnet (text) | JSON | New candidate + 5-10 matches | UNIQUE/DUPLICATE/UNCERTAIN | ~$0.01 | 3-5s |
| 3. ID Verification | Claude Sonnet (vision) | Image | ID doc + claimed data | VERIFIED/FAILED + confidence | ~$0.02 | 5-10s |
| 4. Question Generation | Claude Sonnet (text) | JSON | Profile + target role | 10-15 questions + guide | ~$0.01 | 5-8s |
| 5. Interview Scoring | Claude Sonnet (text) | JSON | Transcript + expected answers | Scores + recommendation | ~$0.01 | 5-8s |

### Agent I/O Examples

See `app/schemas/internal/agent*_io.py` for full Pydantic schemas. Key examples:

**Agent 1 Output:**
```json
{
  "parse_status": "SUCCESS",
  "confidence_score": 0.94,
  "personal_info": { "full_name": "...", "email": "...", "phone": "..." },
  "skills_normalized": [{ "standard_name": "Python", "proficiency": "Advanced", "evidence": "4 years" }],
  "implied_skills": [{ "skill": "Microservices", "inferred_from": "Built microservices", "confidence": 0.85 }],
  "total_experience_years": 6,
  "primary_domain": "FinTech"
}
```

**Agent 5 Output:**
```json
{
  "overall_score": 78,
  "l1_status": "PASSED",
  "evaluation": {
    "technical_knowledge": { "score": 82, "assessment": "Good Python fundamentals" },
    "communication": { "score": 75, "assessment": "Clear responses" }
  },
  "recommendation": "PROCEED_TO_L2",
  "readiness_level": "INTERVIEW_READY"
}
```

---

## Background Processing

### ARQ Worker Architecture

```
┌─────────────────┐     ┌───────────┐     ┌──────────────────┐
│   FastAPI API    │────▶│   Redis   │◀────│   ARQ Worker     │
│  (enqueue job)   │     │  (queue)  │     │  (process job)   │
└─────────────────┘     └───────────┘     └──────┬───────────┘
                                                  │
                                          ┌───────▼───────┐
                                          │  Task Handler  │
                                          │  1. Load data  │
                                          │  2. Call Agent  │
                                          │  3. Save result│
                                          │  4. Update task│
                                          │  5. Emit event │
                                          └───────────────┘
```

### Task Handler Pattern

Every agent handler follows the same pattern:

```python
async def agent1_handler(ctx: dict, task_id: str, candidate_ref: str):
    async with UnitOfWork(session_factory) as uow:
        # 1. Update task status
        task = await uow.tasks.get_by_id(task_id)
        task.status = "PROCESSING"
        task.started_at = utcnow()
        await uow.commit()

        # 2. Load data
        candidate = await uow.candidates_staging.get_by_ref(candidate_ref)
        document = await uow.documents.get_by_id(candidate.resume_document_id)
        file_bytes = await storage.download(document.storage_path)

        # 3. Call agent
        agent = ResumeParserAgent(anthropic_client, PROMPTS_DIR)
        result = await agent.execute(ResumeParserInput(
            candidate_ref=candidate_ref,
            resume_file=base64.b64encode(file_bytes).decode(),
        ))

        # 4. Save result
        candidate.raw_resume_data = result.model_dump()
        candidate.skills_normalized = result.skills_normalized
        candidate.status = "PENDING"
        task.status = "COMPLETED"
        task.result = result.model_dump()
        task.completed_at = utcnow()
        await uow.commit()

        # 5. Emit event
        await event_bus.emit(ResumeParseCompletedEvent(candidate_ref=candidate_ref))
```

---

## API Endpoints

### Candidate Registration
| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `POST` | `/api/v1/candidates/register` | Register candidate (name, email, phone) | API Key |
| `GET` | `/api/v1/candidates/staging` | List staging candidates (paginated) | API Key |
| `GET` | `/api/v1/candidates/staging/{ref}` | Get staging candidate detail | API Key |
| `GET` | `/api/v1/candidates` | List verified candidates (paginated, filterable) | API Key |
| `GET` | `/api/v1/candidates/{ref}` | Get full candidate profile with relations | API Key |

### Agent Endpoints (async — returns `task_id`)
| Method | Path | Input | Auth |
|--------|------|-------|------|
| `POST` | `/api/v1/agent1/parse-resume` | multipart file + candidate_ref | API Key |
| `POST` | `/api/v1/agent2/check-duplicate` | candidate_ref + threshold | API Key |
| `POST` | `/api/v1/agent2/resolve` | candidate_ref + action (MERGE/REJECT/KEEP) | API Key |
| `POST` | `/api/v1/agent3/verify-identity` | multipart image + candidate_ref + doc_type + claimed_data | API Key |
| `POST` | `/api/v1/agent4/generate-questions` | candidate_ref + interview_type + question_config | API Key |
| `POST` | `/api/v1/agent5/score-interview` | interview_ref + transcript | API Key |

### System
| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `GET` | `/api/v1/tasks/{task_id}` | Poll task status + result | API Key |
| `GET` | `/api/v1/skills/taxonomy` | Search skill taxonomy | API Key |
| `POST` | `/api/v1/skills/taxonomy` | Add skill to taxonomy | API Key |
| `GET` | `/health/live` | Liveness probe | None |
| `GET` | `/health/ready` | Readiness probe (checks DB + Redis) | None |

### Response Format

**Success:**
```json
{
  "data": { ... },
  "meta": {
    "request_id": "req_abc123",
    "timestamp": "2026-03-24T10:15:30Z"
  }
}
```

**Error:**
```json
{
  "error": {
    "code": "SR-CAND-001",
    "message": "Candidate not found",
    "detail": "No candidate with ref SR-2024-00999",
    "request_id": "req_abc123"
  }
}
```

---

## Authentication & Security

### POC Phase: API Key Authentication

For the POC phase, all endpoints use API key authentication:

```
Header: X-API-Key: sr_dev_abc123...
```

- Keys are generated as `sr_{environment}_{32_random_hex}` (e.g., `sr_dev_a1b2c3...`)
- Keys are hashed (SHA-256) before storage
- Each key has scopes: `["candidates:read", "candidates:write", "agents:execute"]`
- The raw key is shown once at creation

### Phase 2: Full JWT + RBAC (Designed, Not Yet Implemented)

The auth module is designed to support:
- JWT access tokens (RS256, 15-min expiry) + refresh tokens (7-day, single-use rotation)
- OAuth2 password flow for internal users
- OIDC/SAML for enterprise SSO
- Permission-based RBAC (roles are permission containers)

**Default RBAC Roles:**

| Role | Permissions |
|------|------------|
| `platform_admin` | `*` (all) |
| `tenant_admin` | `candidates:*`, `taxonomy:*`, `users:*` |
| `hr_reviewer` | `candidates:read`, `candidates:update`, `staging:read`, `staging:update` |
| `api_consumer` | `candidates:read`, `taxonomy:read` |

### Security Measures

| Measure | Implementation |
|---------|---------------|
| CORS | Configurable allowed origins |
| Rate Limiting | Redis sliding window (1000 req/min default) |
| Security Headers | HSTS, X-Content-Type-Options, CSP |
| Field Encryption | AES-256-GCM for PII (name, email, phone) |
| Request Correlation | X-Request-ID on every request |
| Input Validation | Pydantic v2 strict mode on all endpoints |

---

## Event System

### In-Process Async Event Bus

```python
# Services emit events after successful operations
await event_bus.emit(CandidateVerifiedEvent(
    candidate_ref="SR-2024-00123",
    actor_id=current_user.id,
))

# Multiple handlers process each event
event_bus.subscribe(CandidateVerifiedEvent, audit_handler.handle)
event_bus.subscribe(CandidateVerifiedEvent, webhook_dispatcher.dispatch)
```

### Core Events

| Event | Triggers |
|-------|----------|
| `CandidateRegisteredEvent` | After POST /register |
| `ResumeParseCompletedEvent` | After Agent 1 completes |
| `DuplicateDetectedEvent` | When Agent 2 finds a match |
| `HRReviewRequiredEvent` | When Agent 2 returns UNCERTAIN |
| `CandidateVerifiedEvent` | When moved from staging to main |
| `IdentityVerificationCompletedEvent` | After Agent 3 |
| `QuestionsGeneratedEvent` | After Agent 4 |
| `InterviewScoredEvent` | After Agent 5 |
| `CandidateEnteredTalentPoolEvent` | When score >= 60% |

### Event Handlers

| Handler | Purpose |
|---------|---------|
| `audit_handler` | Writes to immutable `audit_logs` table |
| `notification_handler` | Sends email notifications (HR review, status updates) |
| `webhook_dispatcher` | Enqueues outbound webhook delivery via ARQ |
| `integration_handler` | Relays events to ATS/LMS integrations |

---

## Error Handling

### Exception Hierarchy

```
SmartRecruitzError (base)
├── DomainError
│   ├── CandidateNotFoundError
│   ├── DuplicateCandidateError
│   ├── InvalidStatusTransitionError
│   └── TaskNotFoundError
├── AuthError
│   ├── AuthenticationFailedError
│   ├── InvalidAPIKeyError
│   └── InsufficientPermissionsError
├── AgentError
│   ├── AgentTimeoutError
│   ├── AgentResponseParseError
│   └── AgentResponseValidationError
├── ValidationError
│   ├── SchemaValidationError
│   └── FileValidationError
└── InfrastructureError
    ├── DatabaseConnectionError
    └── StorageError
```

### Error Code System

Format: `SR-{CATEGORY}-{NUMBER}`

| Category | Range | Examples |
|----------|-------|---------|
| AUTH | SR-AUTH-001-099 | 001: invalid credentials, 002: token expired, 003: insufficient permissions |
| CAND | SR-CAND-001-099 | 001: not found, 002: duplicate email, 003: invalid status transition |
| AGENT | SR-AGENT-001-099 | 001: timeout, 002: parse failure, 003: confidence too low |
| SYS | SR-SYS-001-099 | 001: database unavailable, 002: redis unavailable |

### HTTP Status Mapping

| Exception Type | HTTP Status |
|---------------|-------------|
| DomainError | 404 / 409 / 422 |
| AuthError | 401 / 403 |
| ValidationError | 422 |
| AgentError | 502 |
| InfrastructureError | 503 |
| Unhandled | 500 (generic message, full trace logged) |

---

## Observability

### Structured Logging (structlog)

Every log entry includes context automatically:

```json
{
  "timestamp": "2026-03-24T10:15:30.123Z",
  "level": "info",
  "event": "agent1_completed",
  "request_id": "req_abc123",
  "candidate_ref": "SR-2024-00123",
  "duration_ms": 7230,
  "confidence_score": 0.94,
  "tokens_used": 1847
}
```

### Prometheus Metrics

| Metric | Type | Labels |
|--------|------|--------|
| `sr_http_requests_total` | Counter | method, path, status_code |
| `sr_http_request_duration_seconds` | Histogram | method, path |
| `sr_agent_calls_total` | Counter | agent_name, status |
| `sr_agent_call_duration_seconds` | Histogram | agent_name |
| `sr_agent_tokens_used_total` | Counter | agent_name, token_type |
| `sr_background_tasks_total` | Counter | task_type, status |

### Health Checks

**`GET /health/live`** — Process alive (200 if running)

**`GET /health/ready`** — Dependencies alive:
```json
{
  "status": "healthy",
  "checks": {
    "database": { "status": "up", "latency_ms": 2 },
    "redis": { "status": "up", "latency_ms": 1 },
    "storage": { "status": "up" }
  }
}
```

---

## Configuration

### Environment Variables

All configuration is driven by `app/config/settings.py` (Pydantic `BaseSettings`):

```python
class Settings(BaseSettings):
    # Application
    APP_NAME: str = "SmartRecruitz"
    APP_ENV: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: PostgresDsn
    DB_POOL_SIZE: int = 20

    # Redis
    REDIS_URL: RedisDsn

    # Anthropic
    ANTHROPIC_API_KEY: SecretStr
    ANTHROPIC_MODEL: str = "claude-sonnet-4-20250514"
    ANTHROPIC_TIMEOUT_SECONDS: int = 30

    # Storage
    STORAGE_BACKEND: Literal["local", "s3"] = "local"
    LOCAL_STORAGE_PATH: Path = Path("./uploads")
    S3_BUCKET_NAME: str = ""

    # Security
    API_KEY_SECRET: SecretStr
    FIELD_ENCRYPTION_KEY: SecretStr

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 1000
```

### .env.example

```env
# Application
APP_ENV=development
DEBUG=true
LOG_LEVEL=DEBUG

# Database
DATABASE_URL=postgresql+asyncpg://sr_user:sr_password@localhost:5432/smartrecruitz

# Redis
REDIS_URL=redis://localhost:6379/0

# Anthropic AI
ANTHROPIC_API_KEY=sk-ant-...your-key-here...
ANTHROPIC_MODEL=claude-sonnet-4-20250514

# Storage
STORAGE_BACKEND=local
LOCAL_STORAGE_PATH=./uploads

# Security
API_KEY_SECRET=change-this-to-a-random-string
FIELD_ENCRYPTION_KEY=base64-encoded-32-byte-key
```

---

## Testing Strategy

### Test Pyramid

| Level | % of tests | Database | Claude API | Execution |
|-------|-----------|----------|-----------|-----------|
| Unit | 70% | Mocked | Mocked | < 2 min |
| Integration | 25% | Real (test DB) | Mocked | < 5 min |
| E2E | 5% | Real (test DB) | Mocked | < 10 min |

### Agent Mocking Pattern

```python
@pytest.fixture
def mock_anthropic():
    client = AsyncMock(spec=AnthropicClient)
    fixture = Path("tests/fixtures/agent1_response.json").read_text()
    client.create_message.return_value = MockMessage(
        content=[MockContentBlock(text=fixture)]
    )
    return client

@pytest.fixture
def agent1(mock_anthropic):
    return ResumeParserAgent(client=mock_anthropic, prompt_dir=PROMPTS_DIR)
```

### Running Tests

```bash
make test              # All tests
make test-unit         # Unit tests only
make test-int          # Integration tests (requires Docker DB)
make test-e2e          # E2E tests (requires Docker DB)
make test-cov          # With coverage report
```

---

## Docker & Deployment

### Docker Compose (Development)

```bash
docker compose -f docker/docker-compose.yml up -d
```

Services:
- **postgres**: PostgreSQL 16 on port 5432
- **redis**: Redis 7 on port 6379
- **api**: FastAPI on port 8000
- **worker**: ARQ worker (same image, different CMD)

### Multi-Stage Dockerfile

```dockerfile
# Stage 1: Builder
FROM python:3.12-slim AS builder
WORKDIR /build
COPY pyproject.toml .
RUN pip install --no-cache-dir --target=/deps .

# Stage 2: Runtime
FROM python:3.12-slim AS runtime
RUN adduser --disabled-password --no-create-home appuser
WORKDIR /app
COPY --from=builder /deps /usr/local/lib/python3.12/site-packages
COPY app/ ./app/
USER appuser
EXPOSE 8000
CMD ["uvicorn", "app.asgi:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

---

## Development Guide

### Prerequisites

- Python 3.12+
- Docker & Docker Compose
- Anthropic API key

### Quick Start

```bash
# 1. Start infrastructure
docker compose -f docker/docker-compose.yml up -d postgres redis

# 2. Set up Python environment
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# 3. Configure
cp .env.example .env
# Edit .env with your ANTHROPIC_API_KEY

# 4. Run migrations
make migrate

# 5. Seed data
make seed

# 6. Start development server
make dev   # Starts API on :8000 + worker
```

### Makefile Targets

```
make dev          # Start uvicorn --reload + ARQ worker
make test         # Run all tests
make test-unit    # Unit tests only
make test-int     # Integration tests
make lint         # ruff check + ruff format --check
make typecheck    # mypy --strict
make migrate      # alembic upgrade head
make migrate-new  # alembic revision --autogenerate -m "..."
make seed         # Run seed_runner.py
make docker-up    # docker compose up -d
make docker-down  # docker compose down
```

### API Documentation

FastAPI auto-generates OpenAPI documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

---

## Candidate Status Flow

```
PENDING (staging)
    ├──→ DUPLICATE_REVIEW ──→ REJECTED / HR resolves
    │
    ▼ (unique)
VERIFIED (main) ──→ IDENTITY_VERIFIED ──→ INTERVIEW_READY ──→ TALENT_POOL
                         │                       │
                    VERIFICATION_FAILED     INTERVIEW_FAILED (retry 30 days)
```

---

## License

Proprietary - ZennialPro Private Limited. All rights reserved.
