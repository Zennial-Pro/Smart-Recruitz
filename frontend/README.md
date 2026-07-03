# SmartRecruitz Frontend

**Enterprise-Grade Next.js Frontend for Verified Talent Infrastructure**

---

## Table of Contents

1. [Tech Stack](#tech-stack)
2. [Architecture Overview](#architecture-overview)
3. [Monorepo Structure](#monorepo-structure)
4. [Applications](#applications)
5. [Shared Packages](#shared-packages)
6. [Key Architectural Patterns](#key-architectural-patterns)
7. [Component Architecture](#component-architecture)
8. [State Management](#state-management)
9. [API Integration](#api-integration)
10. [Authentication & RBAC](#authentication--rbac)
11. [Testing Strategy](#testing-strategy)
12. [Build & Deployment](#build--deployment)
13. [Development Guide](#development-guide)

---

## Tech Stack

| Concern | Technology | Version | Rationale |
|---------|-----------|---------|-----------|
| **Framework** | Next.js (App Router) | 15+ | SSR/SSG, routing, middleware, RSC support |
| **Language** | TypeScript | 5.x | Non-negotiable for enterprise codebase |
| **UI Library** | shadcn/ui + Radix UI | latest | Accessible, copy-paste components — we own the code |
| **Styling** | Tailwind CSS | 4 | Utility-first, design tokens, zero runtime |
| **Client State** | Zustand | latest | Minimal boilerplate, TypeScript-native |
| **Server State** | TanStack Query | v5 | Caching, polling, background refetch, optimistic updates |
| **Forms** | React Hook Form + Zod | latest | Performant uncontrolled forms, type-safe validation |
| **API Client** | ky | latest | 3KB fetch wrapper with retry, timeout, hooks |
| **Type Generation** | openapi-typescript | latest | Auto-generate TS types from FastAPI OpenAPI spec |
| **File Upload** | react-dropzone | latest | Drag-drop UX for resumes and ID documents |
| **Charts** | Recharts | latest | React-native composable charts for dashboards |
| **Auth** | NextAuth.js (Auth.js) | v5 | OIDC/SAML SSO, magic links, session management |
| **Internationalization** | next-intl | latest | App Router compatible, ICU syntax, RSC support |
| **Monorepo** | Turborepo | latest | Parallel builds, remote caching, dependency graph |
| **Package Manager** | pnpm | latest | Strict resolution, disk-efficient, workspace protocol |
| **Unit Testing** | Vitest + React Testing Library | latest | Fast, Vite-native, behavior-focused |
| **E2E Testing** | Playwright | latest | Cross-browser, reliable, CI-friendly |
| **Linting** | ESLint + Prettier | latest | Consistent code style |

---

## Architecture Overview

### Two Applications, Shared Foundation

```
┌──────────────────────────────────────────────────────────────┐
│                    Turborepo Monorepo                         │
│                                                              │
│  ┌─────────────────────┐    ┌─────────────────────────────┐ │
│  │  Candidate Portal   │    │  Hiring Manager Portal      │ │
│  │  (apps/candidate)   │    │  (apps/hiring)              │ │
│  │                     │    │                             │ │
│  │  Chatbot-style      │    │  Dashboard with KPIs,      │ │
│  │  onboarding flow    │    │  candidate search,         │ │
│  │  (7 steps)          │    │  talent pool management    │ │
│  └──────────┬──────────┘    └──────────────┬──────────────┘ │
│             │         Shared Packages       │               │
│  ┌──────────▼──────────────────────────────▼──────────────┐ │
│  │  packages/                                             │ │
│  │  ├── ui/            Radix + shadcn components          │ │
│  │  ├── api-client/    ky + OpenAPI types + task polling  │ │
│  │  ├── shared-types/  Domain types matching backend      │ │
│  │  ├── auth/          NextAuth config, RBAC guards       │ │
│  │  ├── hooks/         Shared React hooks                 │ │
│  │  ├── utils/         Pure utility functions             │ │
│  │  └── audit/         Frontend audit logging             │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  tooling/                                              │ │
│  │  ├── eslint-config/    Shared lint rules               │ │
│  │  ├── typescript-config/ Shared tsconfig                │ │
│  │  └── tailwind-config/  Design tokens + presets         │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
                              │
                         HTTP / REST
                              │
                    ┌─────────▼─────────┐
                    │  FastAPI Backend   │
                    │  (port 8000)       │
                    └───────────────────┘
```

### Data Flow: Agent Task Polling

The most critical frontend pattern — handling async AI agent calls:

```
User Action (e.g., upload resume)
    │
    ▼
POST /api/v1/agent1/parse-resume → receives { task_id }
    │
    ▼
Start polling GET /api/v1/tasks/{task_id}
    │
    ├── 2s → { status: "QUEUED" }      → Show "Queued..." animation
    ├── 4s → { status: "PROCESSING" }  → Show "AI analyzing..." animation
    ├── 8s → { status: "PROCESSING" }  → Continue animation
    └── 10s → { status: "COMPLETED", result: {...} } → Display results
                                                        Stop polling
```

Polling uses exponential backoff: 2s → 4s → 8s, capped at 10s. Timeout at 2 minutes.

---

## Monorepo Structure

```
frontend/
├── .github/
│   ├── workflows/
│   │   ├── ci.yml                          # lint + typecheck + test + build
│   │   ├── e2e.yml                         # Playwright against staging
│   │   └── deploy.yml                      # Vercel/Docker deploy
│   └── CODEOWNERS
├── .husky/
│   ├── pre-commit                          # lint-staged
│   └── commit-msg                          # commitlint (conventional commits)
├── turbo.json                              # Turborepo pipeline config
├── pnpm-workspace.yaml                     # Workspace definition
├── package.json                            # Root scripts
├── tsconfig.base.json                      # Shared TypeScript config
├── .eslintrc.base.js                       # Shared ESLint config
├── .prettierrc                             # Formatting rules
│
├── apps/
│   ├── candidate-portal/                   # Candidate chatbot onboarding
│   └── hiring-portal/                      # Hiring Manager dashboard
│
├── packages/
│   ├── ui/                                 # Shared UI component library
│   ├── api-client/                         # API integration layer
│   ├── shared-types/                       # Domain types
│   ├── auth/                               # Auth utilities + RBAC
│   ├── hooks/                              # Shared React hooks
│   ├── utils/                              # Pure utility functions
│   ├── audit/                              # Frontend audit logging
│   └── config/                             # Shared tool configs
│
├── tooling/
│   ├── eslint-config/                      # ESLint preset packages
│   ├── typescript-config/                  # tsconfig preset packages
│   └── tailwind-config/                    # Tailwind preset with design tokens
│
└── README.md                               # This file
```

---

## Applications

### Candidate Portal (`apps/candidate-portal/`)

A **chatbot-style onboarding flow** where candidates register, upload resumes, verify identity, and complete interviews.

```
apps/candidate-portal/
├── next.config.ts
├── tailwind.config.ts                      # Extends tooling/tailwind-config
├── package.json
├── tsconfig.json
├── public/
│   ├── locales/                            # i18n message files
│   │   ├── en/
│   │   └── hi/
│   └── assets/
└── src/
    ├── app/                                # Next.js App Router
    │   ├── layout.tsx                      # Root layout: providers, fonts, metadata
    │   ├── page.tsx                        # Landing / entry redirect
    │   ├── globals.css                     # Tailwind imports + CSS variables
    │   ├── (auth)/                         # Route group — unauthenticated
    │   │   ├── login/page.tsx
    │   │   └── layout.tsx
    │   └── (onboarding)/                   # Route group — main chatbot flow
    │       ├── layout.tsx                  # ProgressTracker header + ChatShell
    │       ├── registration/page.tsx       # Step 1: Name, email, phone
    │       ├── resume-upload/page.tsx      # Step 2: Drag-drop upload + Agent 1
    │       ├── resume-review/page.tsx      # Step 2b: Review parsed data, edit
    │       ├── duplicate-check/page.tsx    # Step 3: Agent 2 auto-processing
    │       ├── id-verification/page.tsx    # Step 4: Upload ID + Agent 3
    │       ├── interview-prep/page.tsx     # Step 5: Agent 4 question generation
    │       ├── interview/page.tsx          # Step 6: Video interview flow
    │       ├── results/page.tsx            # Step 7: Agent 5 scoring + results
    │       └── talent-pool/page.tsx        # Final: Success / failure state
    ├── components/
    │   ├── chat/
    │   │   ├── ChatShell.tsx               # Main chat container with scroll
    │   │   ├── ChatMessage.tsx             # Polymorphic message bubble
    │   │   ├── TypingIndicator.tsx         # Three-dot animation
    │   │   ├── ChatInput.tsx               # Text input + send button
    │   │   ├── ChipSelector.tsx            # Quick-reply chip buttons
    │   │   └── MessageRenderer.tsx         # Routes message type to component
    │   ├── onboarding/
    │   │   ├── ProgressTracker.tsx         # Step circles in header
    │   │   ├── RegistrationForm.tsx        # Name/email/phone form
    │   │   ├── ResumeUploader.tsx          # Drag-drop with progress
    │   │   ├── ParsedResumeReview.tsx      # Editable parsed data display
    │   │   ├── SkillTagsDisplay.tsx        # Color-coded skill tags
    │   │   ├── IdDocumentUploader.tsx      # ID upload with preview
    │   │   ├── VerificationStatus.tsx      # Agent 3 result display
    │   │   ├── InterviewQuestionCard.tsx   # Single question display
    │   │   ├── InterviewQuestionList.tsx   # All questions
    │   │   └── ScoreDashboard.tsx          # Final scores + breakdown
    │   └── shared/
    │       ├── DataCard.tsx                # Info card (from prototype)
    │       ├── StatusBadge.tsx             # Processing/success/failed
    │       ├── ProcessingIndicator.tsx     # AI processing animation
    │       └── FileUploadZone.tsx          # Reusable drag-drop zone
    ├── hooks/
    │   ├── useOnboardingFlow.ts            # State machine for chatbot steps
    │   ├── useTaskPolling.ts               # Polls /tasks/{id} with backoff
    │   ├── useFileUpload.ts                # Upload with progress tracking
    │   └── useChatMessages.ts              # Chat message queue management
    ├── stores/
    │   ├── onboarding-store.ts             # Zustand: step, candidate data, flow
    │   └── chat-store.ts                   # Zustand: message history, typing
    ├── lib/
    │   ├── flow-machine.ts                 # FSM for onboarding step transitions
    │   ├── validators.ts                   # Zod schemas for candidate forms
    │   └── message-templates.ts            # Bot message content templates
    └── types/
        └── onboarding.ts                   # App-specific types
```

#### Onboarding Flow States

```
REGISTRATION → RESUME_UPLOAD → RESUME_REVIEW → DUPLICATE_CHECK →
ID_VERIFICATION → INTERVIEW_PREP → INTERVIEW → RESULTS → TALENT_POOL
```

Each state knows:
- Which page/route renders
- Which agent it triggers (if any)
- What the user sees while AI processes
- What happens on success/failure
- What the next state is

State is persisted to `sessionStorage` so users can resume mid-flow.

---

### Hiring Manager Portal (`apps/hiring-portal/`)

A **dashboard application** for hiring managers to browse verified talent, manage interviews, and review flagged candidates.

```
apps/hiring-portal/
├── next.config.ts
├── tailwind.config.ts
├── package.json
├── tsconfig.json
├── public/locales/
└── src/
    ├── app/
    │   ├── layout.tsx                      # Root: sidebar nav + top bar
    │   ├── page.tsx                        # Redirect to /dashboard
    │   ├── globals.css
    │   ├── (auth)/
    │   │   └── login/page.tsx
    │   └── (dashboard)/                    # Authenticated route group
    │       ├── layout.tsx                  # Sidebar + breadcrumbs
    │       ├── dashboard/page.tsx          # KPI cards + overview charts
    │       ├── candidates/
    │       │   ├── page.tsx                # Candidate list with filters
    │       │   └── [ref]/
    │       │       ├── page.tsx            # Profile overview
    │       │       ├── skills/page.tsx     # Skills radar + taxonomy
    │       │       ├── experience/page.tsx # Experience timeline
    │       │       ├── interview/page.tsx  # Interview scores + Q&A
    │       │       └── verification/page.tsx
    │       ├── talent-pool/
    │       │   ├── page.tsx                # Talent pool browser
    │       │   └── [ref]/page.tsx
    │       ├── search/
    │       │   └── page.tsx                # Skill search + JD upload
    │       ├── interviews/
    │       │   ├── page.tsx                # Interview management list
    │       │   └── [ref]/page.tsx
    │       ├── review-queue/
    │       │   └── page.tsx                # HR review (uncertain duplicates)
    │       └── settings/
    │           ├── page.tsx                # General settings
    │           ├── team/page.tsx           # Team management
    │           └── audit-log/page.tsx      # Audit trail viewer
    ├── components/
    │   ├── layout/
    │   │   ├── Sidebar.tsx                 # Navigation sidebar
    │   │   ├── TopBar.tsx                  # Breadcrumbs + user menu
    │   │   └── Breadcrumbs.tsx
    │   ├── dashboard/
    │   │   ├── KpiCard.tsx                 # Stat card with trend
    │   │   ├── KpiGrid.tsx                 # 4-column layout
    │   │   ├── CandidatePipelineChart.tsx  # Funnel chart
    │   │   ├── TalentPoolGrowthChart.tsx   # Line chart
    │   │   └── RecentActivityFeed.tsx
    │   ├── candidates/
    │   │   ├── CandidateListTable.tsx      # Sortable, paginated table
    │   │   ├── CandidateFilters.tsx        # Skill, domain, status filters
    │   │   ├── CandidateCard.tsx           # Card view layout
    │   │   ├── CandidateProfileHeader.tsx  # Name, badges, status
    │   │   ├── SkillsRadarChart.tsx        # Recharts radar
    │   │   ├── ExperienceTimeline.tsx      # Vertical timeline
    │   │   ├── InterviewScoreBreakdown.tsx # Per-question scores
    │   │   └── VerificationBadge.tsx
    │   ├── search/
    │   │   ├── SkillAutocomplete.tsx       # Taxonomy-backed autocomplete
    │   │   ├── SearchResultsList.tsx       # Ranked candidates
    │   │   └── MatchScoreBadge.tsx
    │   └── review-queue/
    │       ├── ReviewQueueTable.tsx
    │       ├── DuplicateComparisonView.tsx # Side-by-side compare
    │       └── ReviewActionButtons.tsx     # Merge/Reject/Keep
    ├── hooks/
    │   ├── useCandidateSearch.ts           # Debounced search + filters
    │   ├── useSkillTaxonomy.ts             # Fetches + caches taxonomy
    │   ├── useDashboardKpis.ts             # KPI data
    │   └── useReviewQueue.ts
    ├── stores/
    │   ├── filter-store.ts                 # Active filters, search params
    │   └── ui-store.ts                     # Sidebar state, view mode
    ├── lib/
    │   ├── search-utils.ts
    │   ├── chart-config.ts                 # Recharts theme/config
    │   └── validators.ts
    └── types/
        └── hiring.ts
```

#### Dashboard KPIs

| KPI | Source |
|-----|--------|
| Total Candidates | `GET /candidates?count_only=true` |
| Talent Pool Size | `GET /candidates?status=TALENT_POOL&count_only=true` |
| Pending Reviews | `GET /candidates/staging?status=AWAITING_HR_REVIEW&count_only=true` |
| Avg Readiness Score | `GET /candidates?status=TALENT_POOL&aggregate=readiness_score` |
| Pipeline by Status | Candidate count grouped by status |
| Talent Pool Growth | Time-series of talent pool entries |

---

## Shared Packages

### `packages/ui/` — Component Library

shadcn/ui-based components — we own the code, not a dependency.

```
packages/ui/
├── src/
│   ├── primitives/                         # Radix-based accessible components
│   │   ├── Button.tsx
│   │   ├── Input.tsx
│   │   ├── Select.tsx
│   │   ├── Dialog.tsx
│   │   ├── Tabs.tsx
│   │   ├── Tooltip.tsx
│   │   ├── Popover.tsx
│   │   ├── DropdownMenu.tsx
│   │   ├── Table.tsx
│   │   ├── Badge.tsx
│   │   ├── Card.tsx
│   │   ├── Skeleton.tsx
│   │   ├── Toast.tsx
│   │   ├── Progress.tsx
│   │   └── Avatar.tsx
│   ├── composed/                           # Reusable patterns
│   │   ├── FileDropzone.tsx                # Drag-drop file upload area
│   │   ├── SearchInput.tsx                 # Input with search icon + clear
│   │   ├── TagInput.tsx                    # Add/remove tags
│   │   ├── DataTable.tsx                   # Sortable, paginated table shell
│   │   ├── EmptyState.tsx                  # Configurable empty state
│   │   ├── LoadingOverlay.tsx
│   │   ├── ConfirmDialog.tsx
│   │   └── FormField.tsx                   # Label + input + error message
│   └── theme/
│       ├── tokens.ts                       # Design tokens as TS constants
│       └── cn.ts                           # clsx + twMerge utility
```

### `packages/api-client/` — API Integration

```
packages/api-client/
├── src/
│   ├── client.ts                           # Configured ky instance
│   ├── interceptors/
│   │   ├── auth.ts                         # Attach API key / JWT to requests
│   │   ├── error.ts                        # Transform HTTP errors → typed ApiError
│   │   ├── audit.ts                        # Log API calls for audit trail
│   │   └── tenant.ts                       # Attach X-Tenant-Id header
│   ├── endpoints/
│   │   ├── candidates.ts                   # /candidates/* wrappers
│   │   ├── agents.ts                       # /agent1-5/* wrappers
│   │   ├── tasks.ts                        # /tasks/* + polling helper
│   │   ├── skills.ts                       # /skills/* wrappers
│   │   ├── interviews.ts
│   │   └── documents.ts
│   ├── generated/
│   │   └── schema.ts                       # Auto-generated from OpenAPI spec
│   └── polling/
│       ├── task-poller.ts                  # Exponential backoff polling
│       └── types.ts                        # TaskStatus, TaskResult types
```

### `packages/shared-types/` — Domain Types

```
packages/shared-types/
├── src/
│   ├── candidate.ts                        # CandidateStaging, CandidateMain
│   ├── verification.ts                     # Verification, DocumentType
│   ├── interview.ts                        # Interview, InterviewQuestion
│   ├── skill.ts                            # SkillTaxonomy, Proficiency
│   ├── task.ts                             # BackgroundTask, TaskStatus
│   ├── agent-io.ts                         # Agent1-5 Input/Output types
│   ├── enums.ts                            # All status enums (matching backend)
│   └── api.ts                              # PaginatedResponse, ApiError
```

### `packages/auth/` — Authentication & RBAC

```
packages/auth/
├── src/
│   ├── provider.tsx                        # AuthProvider React context
│   ├── hooks.ts                            # useAuth, usePermission, useRole
│   ├── rbac.ts                             # Role definitions, permission checking
│   ├── guards.tsx                          # RouteGuard, PermissionGate components
│   ├── types.ts                            # User, Role, Permission types
│   └── middleware.ts                       # Next.js middleware helper
```

### `packages/audit/` — Frontend Audit Logging

```
packages/audit/
├── src/
│   ├── logger.ts                           # AuditLogger class
│   ├── events.ts                           # Typed audit event definitions
│   ├── hooks.ts                            # useAuditLog hook
│   └── transport.ts                        # Batch + send to backend
```

---

## Key Architectural Patterns

### 1. Task Polling with TanStack Query

The `useAgentTask` hook handles the full lifecycle:

```typescript
function useAgentTask<TResult>(options: {
  mutationFn: (input: any) => Promise<{ task_id: string }>;
  onSuccess?: (result: TResult) => void;
}) {
  // 1. Submit mutation (POST to agent endpoint)
  // 2. On success, extract task_id
  // 3. Start polling with useQuery + refetchInterval
  //    - Interval: 2s → 4s → 8s → 10s (exponential backoff, capped)
  //    - Stop when status is COMPLETED or FAILED
  // 4. Return { status, result, error, isPolling, progress }
}
```

### 2. Onboarding State Machine

A typed finite state machine governs the candidate flow:

```typescript
type OnboardingState =
  | "REGISTRATION"
  | "RESUME_UPLOAD"
  | "RESUME_REVIEW"
  | "DUPLICATE_CHECK"
  | "ID_VERIFICATION"
  | "INTERVIEW_PREP"
  | "INTERVIEW"
  | "RESULTS"
  | "TALENT_POOL";

type OnboardingEvent =
  | { type: "REGISTRATION_COMPLETE"; candidateRef: string }
  | { type: "RESUME_PARSED"; data: ResumeParseResult }
  | { type: "RESUME_REVIEWED" }
  | { type: "DUPLICATE_CHECK_PASSED" }
  | { type: "IDENTITY_VERIFIED" }
  | { type: "QUESTIONS_GENERATED" }
  | { type: "INTERVIEW_COMPLETED"; transcript: string }
  | { type: "SCORING_COMPLETE"; score: number };
```

State persisted to `sessionStorage` — users can resume mid-flow.

### 3. Polymorphic Chat Messages

The `ChatMessage` component renders different content based on message type:

| Message Type | Renders |
|---|---|
| `text` | Simple text bubble |
| `data-card` | Structured key-value card (registration summary, parsed resume) |
| `file-upload` | Inline drag-drop zone |
| `chips` | Quick-reply button row |
| `processing` | AI processing animation with progress bar |
| `skill-tags` | Color-coded skill badges by proficiency |
| `score-card` | Interview score breakdown with charts |
| `verification` | ID verification result with confidence |

### 4. Authentication

**Candidate Portal:**
- Email-based magic link or OTP (no passwords for a one-time flow)
- Optional OAuth (Google/LinkedIn) for convenience

**Hiring Manager Portal:**
- Enterprise SSO via OIDC (Okta, Azure AD, Google Workspace)
- Fallback to email/password

### 5. RBAC on Frontend

```tsx
// Route-level protection via Next.js middleware
export function middleware(request: NextRequest) {
  const session = await getToken({ req: request });
  if (!session) return redirect("/login");
  if (!hasRole(session, "HIRING_MANAGER")) return redirect("/unauthorized");
}

// Component-level protection
<PermissionGate permission="review-queue:action">
  <ReviewActionButtons />
</PermissionGate>
```

**Roles:** `CANDIDATE`, `HIRING_MANAGER`, `HR_ADMIN`, `SUPER_ADMIN`

### 6. Error Handling (3 layers)

1. **API Client** (`interceptors/error.ts`): Catches HTTP errors → typed `ApiError`. Handles 401 (redirect), 429 (backoff), 5xx (retry).
2. **TanStack Query**: Global `onError` → toast notifications. Per-query error handling.
3. **UI Layer**: React Error Boundaries at route level. Next.js `error.tsx` for recovery UI.

### 7. Multi-Tenant Support (Future-Ready)

- Tenant context from JWT claims
- `X-Tenant-Id` header on every API request
- Dynamic theming: CSS custom properties loaded from tenant config
- URL structure: `{tenant}.smartrecruitz.com` via Next.js middleware

---

## Component Architecture

**Approach: Feature-based with shared primitives.**

```
packages/ui/primitives/     → Accessible building blocks (Button, Input, Dialog)
packages/ui/composed/       → Reusable patterns (DataTable, FileDropzone)
apps/*/components/          → Feature-specific (SkillsRadarChart, ChatMessage)
```

Components are **not** organized by atomic design (atoms/molecules/organisms). Instead:
- **Primitives** live in the shared `packages/ui` — used by both apps
- **Composed** components combine primitives into reusable patterns
- **Feature components** are app-specific and live in the respective app's `components/` directory

---

## State Management

### Client State: Zustand

Minimal stores for UI state that doesn't come from the server:

```typescript
// Candidate portal: onboarding flow state
interface OnboardingStore {
  currentStep: OnboardingState;
  candidateRef: string | null;
  candidateData: Partial<CandidateProfile>;
  setStep: (step: OnboardingState) => void;
  setCandidateRef: (ref: string) => void;
  updateCandidateData: (data: Partial<CandidateProfile>) => void;
  reset: () => void;
}

// Hiring portal: filter state
interface FilterStore {
  skills: string[];
  domain: string | null;
  status: CandidateStatus | null;
  experienceRange: [number, number];
  searchQuery: string;
  setFilter: (key: string, value: any) => void;
  resetFilters: () => void;
}
```

### Server State: TanStack Query

All API data is managed by TanStack Query — no manual state for server data:

```typescript
// Fetch candidates with filters
const { data, isLoading } = useQuery({
  queryKey: ["candidates", filters],
  queryFn: () => candidatesApi.list(filters),
});

// Agent task with polling
const { data: task } = useQuery({
  queryKey: ["task", taskId],
  queryFn: () => tasksApi.getStatus(taskId),
  refetchInterval: (query) => {
    const status = query.state.data?.status;
    if (status === "COMPLETED" || status === "FAILED") return false;
    return Math.min(2000 * Math.pow(2, query.state.dataUpdateCount), 10000);
  },
});
```

---

## API Integration

### Type-Safe API Client

Types are auto-generated from the backend's OpenAPI spec:

```bash
# Generate types from running backend
pnpm --filter api-client generate-types
# Runs: openapi-typescript http://localhost:8000/openapi.json -o src/generated/schema.ts
```

### Endpoint Wrappers

```typescript
// packages/api-client/src/endpoints/candidates.ts
export const candidatesApi = {
  register: (data: CandidateRegisterRequest) =>
    client.post("candidates/register", { json: data }).json<CandidateResponse>(),

  list: (params?: CandidateListParams) =>
    client.get("candidates", { searchParams: params }).json<PaginatedResponse<CandidateMain>>(),

  getByRef: (ref: string) =>
    client.get(`candidates/${ref}`).json<CandidateDetailResponse>(),
};
```

### Task Polling Helper

```typescript
// packages/api-client/src/polling/task-poller.ts
export interface TaskPollerOptions {
  taskId: string;
  initialInterval: number;     // 2000ms
  maxInterval: number;         // 10000ms
  backoffMultiplier: number;   // 2
  timeout: number;             // 120000ms
}
```

---

## Testing Strategy

### Unit Tests (Vitest + React Testing Library)

- **Coverage target:** 80% for packages, 70% for app components
- Test hooks: `useAgentTask`, `useTaskPolling`, `useOnboardingFlow`
- Test state machines: step transitions, edge cases
- Test form validations: Zod schemas
- Test RBAC: permission gates, route guards

### Integration Tests (Vitest + MSW)

- Mock Service Worker intercepts API calls
- Test full flows: "submit form → API call → success message"
- Test polling: "submit agent task → poll 3 times → display results"
- Test error flows: "agent fails → error toast → retry works"

### E2E Tests (Playwright)

- **Candidate Portal:** Full onboarding (7 steps) against staging backend
- **Hiring Portal:** Login → search → view profile → take action
- Visual regression with screenshot comparison
- Accessibility audits via axe-core

### Running Tests

```bash
pnpm test              # All unit tests
pnpm test:e2e          # Playwright E2E
pnpm test:coverage     # With coverage report
```

---

## Build & Deployment

### Turborepo Pipeline

```json
{
  "pipeline": {
    "lint": { "dependsOn": [] },
    "typecheck": { "dependsOn": [] },
    "test": { "dependsOn": ["typecheck"] },
    "build": { "dependsOn": ["lint", "typecheck", "test"] }
  }
}
```

Build order (automatic via dependency graph):
1. `packages/ui` + `packages/shared-types` (no deps)
2. `packages/api-client` + `packages/auth` (depend on shared-types)
3. `apps/candidate-portal` + `apps/hiring-portal` (depend on packages)

### Deployment

**Option A: Vercel (Recommended)**
- Each app deploys as separate Vercel project
- `candidate.smartrecruitz.com` → candidate-portal
- `hiring.smartrecruitz.com` → hiring-portal
- Preview deployments per PR
- Edge middleware for auth + routing

**Option B: Docker**
- Each app builds standalone image (`output: 'standalone'`)
- Deploy to K8s with separate Deployments
- Ingress routes by subdomain

### CI Pipeline

1. **PR opened:** lint + typecheck + unit tests + build (cached by Turborepo)
2. **PR merged to main:** build + deploy to staging + Playwright E2E
3. **Release tag:** promote staging to production

---

## Development Guide

### Prerequisites

- Node.js 20+
- pnpm 9+
- Backend running on `localhost:8000` (for API types generation)

### Quick Start

```bash
# 1. Install dependencies
pnpm install

# 2. Generate API types (requires backend running)
pnpm --filter api-client generate-types

# 3. Start both apps in development mode
pnpm dev

# Candidate Portal: http://localhost:3000
# Hiring Portal:    http://localhost:3001
```

### Available Scripts

```bash
pnpm dev                # Start all apps in parallel
pnpm build              # Build all packages + apps
pnpm lint               # Lint all packages + apps
pnpm typecheck          # TypeScript check all
pnpm test               # Run all unit tests
pnpm test:e2e           # Run Playwright E2E tests
pnpm clean              # Clean all node_modules + .next
```

### Adding a New Component to `packages/ui`

1. Create component in `packages/ui/src/primitives/` or `composed/`
2. Export from `packages/ui/src/index.ts`
3. Import in app: `import { Button } from "@smartrecruitz/ui"`

### Environment Variables

```env
# .env.local (not committed)
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your-secret-here
```

---

## Performance Targets

| Metric | Target |
|--------|--------|
| First Load JS per route | < 200KB |
| Largest Contentful Paint | < 2.5s |
| Time to Interactive | < 3.5s |
| Cumulative Layout Shift | < 0.1 |

Achieved via:
- Next.js automatic code splitting per route
- React Server Components for data-heavy pages
- `next/image` for optimized images
- Route prefetching for predictable navigation (onboarding flow)
- Bundle analysis via `@next/bundle-analyzer` in CI

---

## License

Proprietary - ZennialPro Private Limited. All rights reserved.
