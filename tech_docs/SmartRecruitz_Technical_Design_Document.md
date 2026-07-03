# SmartRecruitz — Technical Design Document (TDD)
## Candidate-Side AI Agents — 5 POCs

**Product:** SmartRecruitz — Verified Talent Infrastructure Platform
**Company:** ZennialPro Private Limited
**Scope:** Candidate onboarding pipeline — 5 AI agents
**Version:** 1.0
**Date:** 2026-03-23

---

## 1. What We're Building

5 AI-powered agents that process candidates from resume upload to talent pool entry. Each agent runs independently, called sequentially through a chatbot-style frontend.

**Out of scope (for now):** Hiring Manager side (Agent 6), Authentication/RBAC, LMS integration, Enterprise admin, Reporting dashboards.

---

## 2. Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Backend API | **FastAPI** (Python 3.12, async) | Fast, async, auto-generated docs |
| AI Model | **Claude Sonnet** (Anthropic SDK) | All 5 agents — text + document/image analysis |
| Database | **PostgreSQL** | JSONB for flexible data, relational for structured |
| ORM | **SQLAlchemy** (async) | Type-safe models, async support |
| Migrations | **Alembic** | DB schema versioning |
| Task Queue | **ARQ** + **Redis** | Async background processing (AI calls take 5-15 sec) |
| Validation | **Pydantic** | Input/output schema validation |
| File Storage | **Local disk** (dev) / **S3** (prod) | Resume, ID doc storage |
| Containerization | **Docker** + **Docker Compose** | Postgres, Redis, app, worker |

**No LangChain. No LangGraph.** All agents are single-call to Claude — no chaining, no memory framework needed.

---

## 3. Candidate Pipeline Flow

```
Candidate enters chatbot
        |
        v
[Collect basic info: name, email, phone] --> Save to DB
        |
        v
[Upload Resume]
        |
        v
AGENT 1: Resume Parser + Skill Normalization
   - AI Model: Claude Sonnet (with PDF/image attached)
   - Input: Resume file (PDF/DOCX/Image)
   - AI Does: Reads document directly, extracts all fields,
              normalizes skills to taxonomy, identifies domains,
              infers implied skills
   - Output: Structured candidate profile JSON
   - Storage: candidates_staging (status: PENDING)
   - Also: Quick duplicate pre-check (email/phone exact match against DB)
        |
        v
AGENT 2: Duplicate Detection
   - AI Model: Claude Sonnet (text only)
   - Step 1 (DB - free): Query candidates_main for potential matches
            - Exact email/phone match
            - Fuzzy name match (PostgreSQL pg_trgm)
            - Same company + overlapping dates
            - Narrows 1000s of records --> 5-10 potential matches
   - Step 2 (AI - one call): Send new candidate + 5-10 matches to Claude
            - Semantic name matching (Bob = Robert)
            - Timeline validation
            - Confidence scoring
   - Output: UNIQUE / DUPLICATE / UNCERTAIN
   - If UNIQUE --> Move to candidates_main (status: VERIFIED)
   - If DUPLICATE (>75%) --> Merge or reject
   - If UNCERTAIN (50-75%) --> Flag for HR review
        |
        v
AGENT 3: ID Verification
   - AI Model: Claude Sonnet (with image attached)
   - Input: ID document image (Aadhaar/PAN/Passport) + claimed data from registration
   - AI Does: OCR extraction, tampering detection, compares extracted data vs claimed data
   - Output: VERIFIED / FAILED / MANUAL_REVIEW + confidence score
   - NOTE: We do NOT connect to government databases. We verify internal consistency only.
   - Storage: verifications table
   - If VERIFIED --> status: IDENTITY_VERIFIED
        |
        v
AGENT 4: Interview Question Generation
   - AI Model: Claude Sonnet (text only)
   - Input: Candidate profile (from Agent 1) + target role template
   - AI Does: Generates personalized questions targeting claimed experience,
              checks against question history DB to avoid repetition
   - Output: 10-15 unique questions with expected answer points + interviewer guide
   - Storage: interviews + interview_questions tables
   - Each question is hashed for deduplication
        |
        v
[VIDEO INTERVIEW — External Service (Interview as Service module)]
   - Candidate records video answers
   - Service provides: transcript + genuineness flags (face match, liveness)
   - SmartRecruitz receives transcript only
        |
        v
AGENT 5: Interview Scoring + Readiness
   - AI Model: Claude Sonnet (text only)
   - Input: Interview transcript + expected answers from Agent 4
   - AI Does: Evaluates each answer against expected points,
              scores technical accuracy + communication,
              generates overall readiness score
   - Output: Overall score + pass/fail + per-question breakdown + recommendation
   - If score >= 60% --> status: TALENT_POOL
   - If score < 60% --> status: INTERVIEW_FAILED (can retry after 30 days)
        |
        v
[TALENT POOL — Verified, interviewed, ready for hiring managers]
```

---

## 4. Database Schema

### 4.1 Table Overview

```
candidates_staging (temporary, raw data from Agent 1)
        |
        | Agent 2 moves unique candidates
        v
candidates_main (verified candidates)
   |-- candidate_skills (FK --> skill_taxonomy)
   |-- candidate_experiences
   |-- candidate_educations
   |-- verifications (Agent 3 results)
   |-- interviews --> interview_questions (Agent 4 + Agent 5)

skill_taxonomy (master skill list)
uploaded_documents (resumes, ID docs)
background_tasks (async processing tracker)
```

### 4.2 Table Definitions

#### candidates_staging
Temporary storage. Raw parsed data as JSONB. Deleted/moved after duplicate check.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID (PK) | Auto-generated |
| candidate_ref | VARCHAR(50) | Business key "SR-2024-00123" |
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
| resume_document_id | UUID (FK) | --> uploaded_documents |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

#### candidates_main
Verified candidates with normalized child tables.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID (PK) | |
| candidate_ref | VARCHAR(50) | Unique business key |
| status | VARCHAR(30) | VERIFIED / IDENTITY_VERIFIED / INTERVIEW_READY / TALENT_POOL / INTERVIEW_FAILED / CLOSED |
| full_name | VARCHAR(255) | |
| email | VARCHAR(255) | Unique |
| phone | VARCHAR(50) | Unique |
| current_title | VARCHAR(255) | |
| total_experience_years | FLOAT | |
| primary_domain | VARCHAR(100) | |
| location | VARCHAR(255) | |
| target_role | VARCHAR(255) | Self-declared during registration |
| readiness_score | FLOAT | Set by Agent 5 |
| verification_status | VARCHAR(30) | PENDING / VERIFIED / FAILED |
| talent_pool_entry_date | TIMESTAMP | When they entered talent pool |
| raw_profile_data | JSONB | Complete parsed profile |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

#### candidate_skills

| Column | Type | Description |
|--------|------|-------------|
| id | UUID (PK) | |
| candidate_id | UUID (FK) | --> candidates_main |
| skill_id | UUID (FK) | --> skill_taxonomy |
| proficiency | VARCHAR(20) | BEGINNER / INTERMEDIATE / ADVANCED / EXPERT |
| years_experience | FLOAT | |
| evidence | VARCHAR(500) | "4 years building microservices" |
| is_implied | BOOLEAN | True if inferred by AI |
| confidence | FLOAT | AI confidence for implied skills |

#### candidate_experiences

| Column | Type | Description |
|--------|------|-------------|
| id | UUID (PK) | |
| candidate_id | UUID (FK) | --> candidates_main |
| company | VARCHAR(255) | |
| title | VARCHAR(255) | |
| start_date | VARCHAR(20) | "2020-01" |
| end_date | VARCHAR(20) | Null if current |
| duration_months | INT | |
| domain | VARCHAR(100) | |
| is_current | BOOLEAN | |
| responsibilities | JSONB | Array of strings |

#### candidate_educations

| Column | Type | Description |
|--------|------|-------------|
| id | UUID (PK) | |
| candidate_id | UUID (FK) | --> candidates_main |
| institution | VARCHAR(255) | |
| degree | VARCHAR(100) | |
| field | VARCHAR(255) | |
| graduation_year | INT | |

#### skill_taxonomy
Master skill list. All candidate skills map to this.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID (PK) | |
| standard_name | VARCHAR(255) | "JavaScript" — unique |
| category | VARCHAR(100) | Programming Language, Framework, Cloud, etc. |
| aliases | JSONB | ["JS", "ECMAScript", "Javascript"] |
| parent_skill_id | UUID (FK) | Self-referential for hierarchy |

#### verifications

| Column | Type | Description |
|--------|------|-------------|
| id | UUID (PK) | |
| verification_ref | VARCHAR(50) | "VER-2024-78901" |
| candidate_id | UUID (FK) | --> candidates_main |
| verification_type | VARCHAR(20) | IDENTITY |
| document_type | VARCHAR(30) | AADHAAR_CARD / PAN_CARD / PASSPORT |
| status | VARCHAR(20) | PENDING / VERIFIED / FAILED / MANUAL_REVIEW |
| confidence_score | FLOAT | |
| extracted_data | JSONB | What AI read from document |
| data_match_results | JSONB | Comparison results |
| document_authenticity | JSONB | Fraud indicators, quality score |
| flags | JSONB | Any issues found |
| document_id | UUID (FK) | --> uploaded_documents |
| created_at | TIMESTAMP | |

#### interviews

| Column | Type | Description |
|--------|------|-------------|
| id | UUID (PK) | |
| interview_ref | VARCHAR(50) | "INT-2024-00456" |
| candidate_id | UUID (FK) | --> candidates_main |
| interview_type | VARCHAR(20) | L1_SCREENING |
| status | VARCHAR(30) | QUESTIONS_GENERATED / SCHEDULED / COMPLETED / SCORED |
| transcript | TEXT | Full interview transcript |
| overall_score | FLOAT | Set by Agent 5 |
| l1_status | VARCHAR(20) | PASSED / FAILED |
| recommendation | VARCHAR(30) | PROCEED_TO_L2 / REJECT / MANUAL_REVIEW |
| evaluation_data | JSONB | Full Agent 5 output |
| interviewer_guide | JSONB | Focus areas, red flags |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

#### interview_questions

| Column | Type | Description |
|--------|------|-------------|
| id | UUID (PK) | |
| interview_id | UUID (FK) | --> interviews |
| question_ref | VARCHAR(20) | "Q-001" |
| category | VARCHAR(30) | EXPERIENCE_VERIFICATION / TECHNICAL / BEHAVIORAL |
| question_text | TEXT | The actual question |
| targets_skill | VARCHAR(100) | What skill this tests |
| targets_experience | VARCHAR(255) | What experience claim this verifies |
| difficulty | VARCHAR(20) | MID / SENIOR / LEAD |
| expected_answer_points | JSONB | Array of expected answers |
| follow_up_questions | JSONB | |
| time_estimate_mins | INT | |
| answer_quality | VARCHAR(20) | CORRECT / PARTIAL / INCORRECT (set by Agent 5) |
| answer_score | FLOAT | Set by Agent 5 |
| question_hash | VARCHAR(64) | For deduplication (indexed) |
| created_at | TIMESTAMP | |

#### uploaded_documents

| Column | Type | Description |
|--------|------|-------------|
| id | UUID (PK) | |
| filename | VARCHAR(255) | Stored filename |
| original_filename | VARCHAR(255) | What user uploaded |
| content_type | VARCHAR(100) | "application/pdf", "image/png" |
| file_size_bytes | INT | |
| storage_path | VARCHAR(500) | Path in file storage |
| document_category | VARCHAR(30) | RESUME / ID_DOCUMENT |
| uploaded_by_ref | VARCHAR(50) | candidate_ref |
| created_at | TIMESTAMP | |

#### background_tasks

| Column | Type | Description |
|--------|------|-------------|
| id | UUID (PK) | |
| task_type | VARCHAR(50) | AGENT1_RESUME_PARSE / AGENT2_DUPLICATE / etc. |
| reference_id | VARCHAR(50) | candidate_ref |
| status | VARCHAR(20) | QUEUED / PROCESSING / COMPLETED / FAILED |
| result | JSONB | Agent output when completed |
| error_message | TEXT | If failed |
| created_at | TIMESTAMP | |
| started_at | TIMESTAMP | |
| completed_at | TIMESTAMP | |

---

## 5. API Endpoints

### 5.1 Candidate Registration
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/candidates/register` | Save name, email, phone |
| GET | `/api/v1/candidates/staging` | List staging candidates |
| GET | `/api/v1/candidates/staging/{ref}` | Get staging candidate detail |
| GET | `/api/v1/candidates` | List verified candidates |
| GET | `/api/v1/candidates/{ref}` | Get full candidate profile |

### 5.2 Agent Endpoints
All agent endpoints return a `task_id` immediately (async). Poll `/tasks/{id}` for result.

| Method | Path | Agent | Input |
|--------|------|-------|-------|
| POST | `/api/v1/agent1/parse-resume` | Resume Parser | multipart file + candidate_ref |
| POST | `/api/v1/agent2/check-duplicate` | Duplicate Check | candidate_ref + threshold |
| POST | `/api/v1/agent2/resolve` | HR Resolve | candidate_ref + action (MERGE/REJECT/KEEP) |
| POST | `/api/v1/agent3/verify-identity` | ID Verification | multipart image + candidate_ref + document_type + claimed_data |
| POST | `/api/v1/agent4/generate-questions` | Question Gen | candidate_ref + interview_type + question_config |
| POST | `/api/v1/agent5/score-interview` | Interview Score | interview_ref + transcript |

### 5.3 Task Polling
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/tasks/{task_id}` | Check task status + result |

### 5.4 Skill Taxonomy
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/skills/taxonomy` | List all skills (with search) |
| POST | `/api/v1/skills/taxonomy` | Add skill to taxonomy |

---

## 6. Architecture — 3 Layers

```
┌─────────────────────────────────────────────────────┐
│  API Layer (app/api/v1/)                            │
│  Thin HTTP routes — receives requests, returns      │
│  task_id or results. No business logic here.        │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────v──────────────────────────────┐
│  Service Layer (app/services/)                      │
│  Business logic — DB operations, orchestration,     │
│  moves candidates between tables, triggers agents   │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────v──────────────────────────────┐
│  Agent Layer (app/agents/)                          │
│  Pure AI logic — builds prompts, calls Claude,      │
│  parses responses. No DB access. Testable in        │
│  isolation by mocking Claude.                       │
└─────────────────────────────────────────────────────┘
```

### Background Processing:
```
API receives request
    --> Creates background_task record (status: QUEUED)
    --> Returns task_id to frontend immediately
    --> ARQ worker picks up the job
    --> Worker calls Agent --> Agent calls Claude
    --> Worker saves result to DB
    --> Updates background_task (status: COMPLETED)
    --> Frontend polls /tasks/{id} and gets result
```

---

## 7. Project Folder Structure

```
smartrecruitz/
├── app/
│   ├── main.py                    # FastAPI app
│   ├── config.py                  # Environment settings
│   ├── dependencies.py            # Dependency injection
│   ├── db/                        # Database setup
│   ├── models/                    # SQLAlchemy models (11 tables)
│   ├── schemas/                   # Pydantic input/output models
│   ├── api/v1/                    # Route handlers
│   ├── agents/                    # AI agent logic (5 agents)
│   │   ├── base.py                # Base agent class
│   │   ├── agent1_resume_parser.py
│   │   ├── agent2_duplicate.py
│   │   ├── agent3_verification.py
│   │   ├── agent4_question_gen.py
│   │   ├── agent5_interview_score.py
│   │   └── prompts/               # System prompts as .txt files
│   ├── services/                  # Business logic
│   ├── core/                      # Shared infra (Claude client, file storage, task queue)
│   └── workers/                   # Background task handlers
├── tests/
├── docker-compose.yml             # Postgres + Redis + app + worker
├── Dockerfile
├── pyproject.toml                 # Dependencies
└── .env.example                   # Environment variables
```

---

## 8. Agent Input/Output Summary

### Agent 1 — Resume Parser
**Input:**
```json
{
  "candidate_ref": "SR-2024-00123",
  "resume_file": "<base64 encoded PDF/DOCX/Image>"
}
```
**Output:**
```json
{
  "parse_status": "SUCCESS",
  "confidence_score": 0.94,
  "personal_info": { "full_name": "...", "email": "...", "phone": "..." },
  "experience": [{ "company": "...", "title": "...", "domain": "FinTech", "duration_months": 48 }],
  "education": [{ "institution": "...", "degree": "...", "graduation_year": 2018 }],
  "skills_normalized": [{ "standard_name": "Python", "proficiency": "Advanced", "evidence": "4 years" }],
  "implied_skills": [{ "skill": "Microservices", "inferred_from": "Built microservices", "confidence": 0.85 }],
  "total_experience_years": 6,
  "primary_domain": "FinTech",
  "domain_wise_experience": [{ "domain": "FinTech", "years": 4 }, { "domain": "E-Commerce", "years": 2 }]
}
```

### Agent 2 — Duplicate Detection
**Input:**
```json
{
  "new_candidate": { "name": "Bob Smith", "email": "...", "phone": "...", "experience": [...] },
  "potential_matches_from_db": [
    { "candidate_id": "SR-2023-OLD-123", "name": "Robert Smith", "phone": "same", "experience": [...] }
  ],
  "threshold": 0.75
}
```
**Output:**
```json
{
  "is_duplicate": true,
  "confidence": 0.92,
  "matched_profile": { "candidate_id": "SR-2023-OLD-123" },
  "match_evidence": {
    "phone_match": { "score": 1.0 },
    "name_match": { "score": 0.90, "detail": "Bob = Robert (nickname)" },
    "experience_match": { "score": 0.95 }
  },
  "recommendation": "MERGE_PROFILES"
}
```

### Agent 3 — ID Verification
**Input:**
```json
{
  "document_type": "AADHAAR_CARD",
  "document_image": "<base64 image>",
  "claimed_data": { "full_name": "Rahul Kumar", "date_of_birth": "1995-05-15" }
}
```
**Output:**
```json
{
  "status": "VERIFIED",
  "confidence_score": 96,
  "extracted_data": { "full_name": "Rahul Kumar", "dob": "1995-05-15" },
  "data_match": { "name": { "match": true, "score": 100 }, "dob": { "match": true, "score": 100 } },
  "document_authenticity": { "is_authentic": true, "fraud_indicators": [] }
}
```

### Agent 4 — Question Generation
**Input:**
```json
{
  "candidate_ref": "SR-2024-00123",
  "interview_type": "L1_SCREENING",
  "skill_profile": [{ "skill": "Python", "proficiency": "Expert", "years": 4 }],
  "experience_highlights": [{ "company": "Tech Corp", "key_responsibilities": ["Built microservices"] }],
  "target_role": "Senior Python Developer",
  "question_config": { "total_questions": 12, "difficulty": "MID_SENIOR" }
}
```
**Output:**
```json
{
  "questions": [
    {
      "q_id": "Q-001",
      "category": "EXPERIENCE_VERIFICATION",
      "question": "You mentioned handling 10M requests/day. Walk me through the architecture...",
      "targets_skill": "System Design",
      "difficulty": "SENIOR",
      "expected_answer_points": ["Load balancing", "Caching", "DB optimization"],
      "time_estimate_mins": 5
    }
  ],
  "interviewer_guide": {
    "focus_areas": ["Verify microservices experience", "Assess Python depth"],
    "red_flags": ["Cannot explain architecture in detail"]
  }
}
```

### Agent 5 — Interview Scoring
**Input:**
```json
{
  "interview_ref": "INT-2024-5678",
  "transcript": "INTERVIEWER: Tell me about... CANDIDATE: I worked on...",
  "expected_answers_from_agent4": [{ "question": "...", "expected_points": [...] }]
}
```
**Output:**
```json
{
  "overall_score": 78,
  "l1_status": "PASSED",
  "evaluation": {
    "technical_knowledge": { "score": 82, "assessment": "Good Python fundamentals" },
    "communication": { "score": 75, "assessment": "Clear responses" }
  },
  "answer_validation": [
    { "question": "...", "answer_quality": "CORRECT", "score": 90 }
  ],
  "recommendation": "PROCEED_TO_L2",
  "readiness_level": "INTERVIEW_READY"
}
```

---

## 9. Candidate Status Flow

```
PENDING (staging) --> DUPLICATE_REVIEW / REJECTED
    |
    v (unique)
VERIFIED (main) --> IDENTITY_VERIFIED --> INTERVIEW_READY --> TALENT_POOL
                         |                    |
                    VERIFICATION_FAILED   INTERVIEW_FAILED
```

---

## 10. Cost & Performance

| Agent | Claude Calls | Approx Cost/Candidate | Time |
|-------|-------------|----------------------|------|
| Agent 1 | 1 call (vision) | ~$0.02 | 5-10 sec |
| Agent 2 | 1 call (text) | ~$0.01 | 3-5 sec |
| Agent 3 | 1 call (vision) | ~$0.02 | 5-10 sec |
| Agent 4 | 1 call (text) | ~$0.01 | 5-8 sec |
| Agent 5 | 1 call (text) | ~$0.01 | 5-8 sec |
| **Total** | **5 calls** | **~$0.07/candidate** | **~30-40 sec total** |

**Key optimization:** Agent 2 uses DB filtering first (free), then sends only 5-10 potential matches to AI (one call). Never sends all candidates to AI.

---

## 11. Estimation

| Task | Effort |
|------|--------|
| Foundation (DB, config, Docker, shared infra) | 5-7 days |
| Agent 1 — Resume Parser | 5-7 days |
| Agent 2 — Duplicate Detection | 3-4 days |
| Agent 3 — ID Verification | 3-4 days |
| Agent 4 — Question Generation | 4-5 days |
| Agent 5 — Interview Scoring | 3-4 days |
| Integration + Testing | 4-5 days |
| **Total** | **~28-36 days (1 dev)** |
| | **~15-18 days (2 devs)** |
