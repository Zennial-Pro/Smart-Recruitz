"""Seed 5 test candidates with varying skill matches for the
Full Stack Developer / AI Development JD.

JD skills targeted:
  Python, React, Node.js, FastAPI, Pydantic, Google Cloud Platform,
  Vertex AI, Firestore, BigQuery, Cloud Storage, LLM, Prompt Engineering,
  Agentic AI

Run:
    cd backend && .venv/bin/python scripts/seed_test_candidates.py
"""

import asyncio
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import func, select  # noqa: E402

from app.db.session import async_session_factory  # noqa: E402
from app.models.candidate_education import CandidateEducation  # noqa: E402
from app.models.candidate_experience import CandidateExperience  # noqa: E402
from app.models.candidate_main import CandidateMain  # noqa: E402
from app.models.candidate_skill import CandidateSkill  # noqa: E402
from app.models.interview import Interview  # noqa: E402
from app.models.interview_question import InterviewQuestion  # noqa: E402
from app.models.skill_taxonomy import SkillTaxonomy  # noqa: E402
from app.repositories.interview_repository import PLACEHOLDER_INTERVIEW_VIDEO_URL  # noqa: E402

# Master skill list with categories
SKILL_CATALOG = {
    "Python": "BACKEND",
    "React": "FRONTEND",
    "Node.js": "BACKEND",
    "FastAPI": "BACKEND",
    "Pydantic": "BACKEND",
    "Google Cloud Platform": "CLOUD",
    "Vertex AI": "CLOUD",
    "Firestore": "CLOUD",
    "BigQuery": "CLOUD",
    "Cloud Storage": "CLOUD",
    "LLM": "AI",
    "Prompt Engineering": "AI",
    "Agentic AI": "AI",
    "TypeScript": "FRONTEND",
    "PostgreSQL": "DATABASE",
    "Docker": "DEVOPS",
    "Kubernetes": "DEVOPS",
    "AWS": "CLOUD",
    "Java": "BACKEND",
    "Spring Boot": "BACKEND",
}


# 5 candidates ranked from strongest to weakest match against the JD.
# Each carries full data so every new hiring-manager UI surface is populated:
# resume_analysis (overall + sub-scores + analytics + value-add), linkedin_cross_check,
# CTC / notice / working_status / preferred_location, github + linkedin URLs.
CANDIDATES = [
    {
        "full_name": "Arjun Verma",
        "email": "arjun.verma@example.com",
        "phone": "+91 98765 11111",
        "current_title": "Senior Full Stack Engineer",
        "primary_domain": "AI/ML",
        "location": "Bangalore",
        "target_role": "Senior Full Stack AI Engineer",
        "total_experience_years": 9.0,
        "readiness_score": 92.0,
        # New fields
        "github_url": "https://github.com/arjunverma",
        "linkedin_url": "https://linkedin.com/in/arjun-verma-ai",
        "current_ctc": "32 LPA",
        "expected_ctc": "48 LPA",
        "notice_period": "60 days",
        "working_status": "Currently working",
        "preferred_location": "Bangalore, Remote",
        "resume_overall_score": 92,
        "resume_analysis": {
            "overall_score": 92,
            "summary": "Battle-tested full-stack engineer with strong AI/ML production experience; standout open-source and leadership signals.",
            "sub_scores": {"skills_score": 95, "experience_score": 90, "education_score": 90, "value_add_score": 90},
            "analytics": {
                "skill_count": 13, "avg_tenure_months": 37, "longest_tenure_months": 42,
                "employment_gap_months": 0, "job_count": 3,
                "education_level": "BACHELORS", "top_domain": "AI/ML",
                # 36mo startup (Insight) + 42mo product (Razorpay) + 33mo product (Flipkart)
                "product_experience_years": 6.3, "service_experience_years": 0.0,
                "gcc_experience_years": 0.0, "startup_experience_years": 3.0,
                "dominant_company_type": "PRODUCT",
            },
            "value_add_items": [
                {"category": "ACHIEVEMENT", "description": "Shipped an LLM-based search system serving 40M monthly requests at Razorpay."},
                {"category": "OPEN_SOURCE", "description": "Maintainer of langchain-gcp (2.3k GitHub stars)."},
                {"category": "LEADERSHIP", "description": "Tech lead for a 5-person AI platform team at Insight Solutions."},
                {"category": "CERTIFICATION", "description": "Google Cloud Professional Machine Learning Engineer."},
                {"category": "PUBLICATION", "description": "Blog series on agentic AI in production (50k+ reads)."},
            ],
        },
        "linkedin_cross_check": {
            "match_score": 96,
            "consistent": True,
            "summary": "All companies, titles and dates match between LinkedIn and resume.",
            "mismatches": [],
        },
        "skills": [
            ("Python", "EXPERT", 9.0),
            ("React", "EXPERT", 7.0),
            ("Node.js", "ADVANCED", 5.0),
            ("FastAPI", "EXPERT", 5.0),
            ("Pydantic", "EXPERT", 4.0),
            ("Google Cloud Platform", "ADVANCED", 4.0),
            ("Vertex AI", "ADVANCED", 2.5),
            ("Firestore", "ADVANCED", 3.0),
            ("BigQuery", "ADVANCED", 3.0),
            ("Cloud Storage", "ADVANCED", 4.0),
            ("LLM", "EXPERT", 2.0),
            ("Prompt Engineering", "EXPERT", 2.0),
            ("Agentic AI", "ADVANCED", 1.5),
        ],
        "experiences": [
            {"company": "Insight Solutions", "title": "Senior Full Stack Engineer", "start_date": "2022-01", "end_date": None, "duration_months": 36, "is_current": True, "domain": "AI/ML", "company_type": "STARTUP"},
            {"company": "Razorpay", "title": "Full Stack Developer", "start_date": "2018-06", "end_date": "2021-12", "duration_months": 42, "is_current": False, "domain": "FinTech", "company_type": "PRODUCT"},
            {"company": "Flipkart", "title": "Backend Engineer", "start_date": "2015-08", "end_date": "2018-05", "duration_months": 33, "is_current": False, "domain": "E-Commerce", "company_type": "PRODUCT"},
        ],
        "interview_score": 88.5,
        "l1_status": "PASSED",
    },
    {
        "full_name": "Priya Sharma",
        "email": "priya.sharma@example.com",
        "phone": "+91 98765 22222",
        "current_title": "Full Stack Developer",
        "primary_domain": "Web Development",
        "location": "Gurugram",
        "target_role": "Senior Full Stack Engineer",
        "total_experience_years": 7.0,
        "readiness_score": 78.0,
        "github_url": "https://github.com/priya-sharma",
        "linkedin_url": "https://linkedin.com/in/priya-sharma-eng",
        "current_ctc": "24 LPA",
        "expected_ctc": "36 LPA",
        "notice_period": "30 days",
        "working_status": "Serving notice",
        "preferred_location": "Gurugram, Bangalore, Remote",
        "resume_overall_score": 78,
        "resume_analysis": {
            "overall_score": 78,
            "summary": "Solid full-stack engineer with growing AI/cloud exposure; two strong company tenures.",
            "sub_scores": {"skills_score": 80, "experience_score": 82, "education_score": 75, "value_add_score": 70},
            "analytics": {
                "skill_count": 10, "avg_tenure_months": 44, "longest_tenure_months": 47,
                "employment_gap_months": 0, "job_count": 2,
                "education_level": "BACHELORS", "top_domain": "Web Development",
                # 47mo product (Zomato) + 41mo product (Paytm)
                "product_experience_years": 7.3, "service_experience_years": 0.0,
                "gcc_experience_years": 0.0, "startup_experience_years": 0.0,
                "dominant_company_type": "PRODUCT",
            },
            "value_add_items": [
                {"category": "ACHIEVEMENT", "description": "Reduced Zomato checkout p95 latency by 38% via FastAPI rewrite."},
                {"category": "CERTIFICATION", "description": "Google Cloud Associate Cloud Engineer."},
                {"category": "SIDE_PROJECT", "description": "Built an open-source React component library with 400+ npm weekly downloads."},
            ],
        },
        "linkedin_cross_check": {
            "match_score": 88,
            "consistent": True,
            "summary": "Companies and dates match. Minor title difference at Paytm (resume says 'Software Engineer', LinkedIn says 'SDE II').",
            "mismatches": [
                {"type": "title_drift", "company": "Paytm", "details": "Resume title 'Software Engineer' vs LinkedIn 'SDE II' — same level, different label."},
            ],
        },
        "skills": [
            ("Python", "ADVANCED", 7.0),
            ("React", "ADVANCED", 6.0),
            ("FastAPI", "ADVANCED", 3.0),
            ("Pydantic", "INTERMEDIATE", 2.0),
            ("Google Cloud Platform", "INTERMEDIATE", 2.0),
            ("BigQuery", "INTERMEDIATE", 1.5),
            ("Cloud Storage", "INTERMEDIATE", 2.0),
            ("LLM", "INTERMEDIATE", 1.0),
            ("PostgreSQL", "ADVANCED", 5.0),
            ("Docker", "ADVANCED", 4.0),
        ],
        "experiences": [
            {"company": "Zomato", "title": "Full Stack Developer", "start_date": "2021-03", "end_date": None, "duration_months": 47, "is_current": True, "domain": "Food-Tech", "company_type": "PRODUCT"},
            {"company": "Paytm", "title": "Software Engineer", "start_date": "2017-09", "end_date": "2021-02", "duration_months": 41, "is_current": False, "domain": "FinTech", "company_type": "PRODUCT"},
        ],
        "interview_score": 76.0,
        "l1_status": "PASSED",
    },
    {
        "full_name": "Rahul Iyer",
        "email": "rahul.iyer@example.com",
        "phone": "+91 98765 33333",
        "current_title": "Backend Engineer",
        "primary_domain": "Backend",
        "location": "Bangalore",
        "target_role": "Senior Backend Engineer",
        "total_experience_years": 5.5,
        "readiness_score": 65.0,
        "github_url": "https://github.com/rahuliyer",
        "linkedin_url": "https://linkedin.com/in/rahul-iyer-be",
        "current_ctc": "18 LPA",
        "expected_ctc": "28 LPA",
        "notice_period": "Immediate",
        "working_status": "Not working",
        "preferred_location": "Bangalore",
        "resume_overall_score": 65,
        "resume_analysis": {
            "overall_score": 65,
            "summary": "Capable backend engineer with strong Python/FastAPI core; light on AI exposure and value-add signals.",
            "sub_scores": {"skills_score": 70, "experience_score": 68, "education_score": 65, "value_add_score": 55},
            "analytics": {
                "skill_count": 8, "avg_tenure_months": 37, "longest_tenure_months": 56,
                "employment_gap_months": 0, "job_count": 2,
                "education_level": "BACHELORS", "top_domain": "Backend",
                # 56mo product (Swiggy) + 17mo product (Freshworks)
                "product_experience_years": 6.1, "service_experience_years": 0.0,
                "gcc_experience_years": 0.0, "startup_experience_years": 0.0,
                "dominant_company_type": "PRODUCT",
            },
            "value_add_items": [
                {"category": "ACHIEVEMENT", "description": "Owned Swiggy partner-onboarding API handling 1M requests/day."},
                {"category": "CERTIFICATION", "description": "AWS Certified Solutions Architect Associate."},
            ],
        },
        "linkedin_cross_check": {
            "match_score": 78,
            "consistent": True,
            "summary": "Companies and dates match. One earlier role on LinkedIn not mentioned on resume.",
            "mismatches": [
                {"type": "missing_on_resume", "company": "Capgemini", "details": "LinkedIn shows a 14-month internship at Capgemini before Freshworks that the resume omits."},
            ],
        },
        "skills": [
            ("Python", "ADVANCED", 5.5),
            ("FastAPI", "ADVANCED", 3.0),
            ("Pydantic", "ADVANCED", 2.5),
            ("PostgreSQL", "ADVANCED", 4.0),
            ("Docker", "ADVANCED", 3.0),
            ("Kubernetes", "INTERMEDIATE", 2.0),
            ("AWS", "ADVANCED", 3.0),
            ("Node.js", "INTERMEDIATE", 2.0),
        ],
        "experiences": [
            {"company": "Swiggy", "title": "Backend Engineer", "start_date": "2020-07", "end_date": None, "duration_months": 56, "is_current": True, "domain": "Food-Tech", "company_type": "PRODUCT"},
            {"company": "Freshworks", "title": "Software Engineer", "start_date": "2019-01", "end_date": "2020-06", "duration_months": 17, "is_current": False, "domain": "SaaS", "company_type": "PRODUCT"},
        ],
        "interview_score": 70.0,
        "l1_status": "PASSED",
    },
    {
        "full_name": "Sneha Reddy",
        "email": "sneha.reddy@example.com",
        "phone": "+91 98765 44444",
        "current_title": "Frontend Developer",
        "primary_domain": "Frontend",
        "location": "Hyderabad",
        "target_role": "Senior Frontend Engineer",
        "total_experience_years": 4.0,
        "readiness_score": 58.0,
        "github_url": "https://github.com/sneha-reddy-ui",
        "linkedin_url": "https://linkedin.com/in/sneha-reddy",
        "current_ctc": "14 LPA",
        "expected_ctc": "22 LPA",
        "notice_period": "60 days",
        "working_status": "Currently working",
        "preferred_location": "Hyderabad, Remote",
        "resume_overall_score": 58,
        "resume_analysis": {
            "overall_score": 58,
            "summary": "Strong frontend specialist (React/TS) but limited backend/cloud breadth for full-stack roles.",
            "sub_scores": {"skills_score": 60, "experience_score": 60, "education_score": 60, "value_add_score": 50},
            "analytics": {
                "skill_count": 4, "avg_tenure_months": 29, "longest_tenure_months": 42,
                "employment_gap_months": 0, "job_count": 2,
                "education_level": "BACHELORS", "top_domain": "Frontend",
                # 42mo product (Myntra) + 16mo service (TCS)
                "product_experience_years": 3.5, "service_experience_years": 1.3,
                "gcc_experience_years": 0.0, "startup_experience_years": 0.0,
                "dominant_company_type": "PRODUCT",
            },
            "value_add_items": [
                {"category": "SIDE_PROJECT", "description": "Published a Storybook component library used across two Myntra teams."},
            ],
        },
        "linkedin_cross_check": {
            "match_score": 65,
            "consistent": False,
            "summary": "Companies match but dates are off — resume claims continuous tenure, LinkedIn shows a 4-month gap.",
            "mismatches": [
                {"type": "date_mismatch", "company": "TCS", "details": "Resume: Apr 2020 – Jul 2021. LinkedIn: Aug 2020 – Jul 2021. 4 months overstated."},
                {"type": "title_drift", "company": "Myntra", "details": "Resume: 'Senior Frontend Developer'. LinkedIn: 'Frontend Developer'."},
            ],
        },
        "skills": [
            ("React", "EXPERT", 4.0),
            ("TypeScript", "EXPERT", 3.5),
            ("Node.js", "INTERMEDIATE", 2.0),
            ("Python", "BEGINNER", 0.5),
        ],
        "experiences": [
            {"company": "Myntra", "title": "Frontend Developer", "start_date": "2021-08", "end_date": None, "duration_months": 42, "is_current": True, "domain": "E-Commerce", "company_type": "PRODUCT"},
            {"company": "TCS", "title": "Software Engineer", "start_date": "2020-04", "end_date": "2021-07", "duration_months": 16, "is_current": False, "domain": "IT Services", "company_type": "SERVICE"},
        ],
        "interview_score": 62.0,
        "l1_status": "PASSED",
    },
    {
        "full_name": "Manoj Kumar",
        "email": "manoj.kumar@example.com",
        "phone": "+91 98765 55555",
        "current_title": "Java Developer",
        "primary_domain": "Backend",
        "location": "Pune",
        "target_role": "Senior Java Developer",
        "total_experience_years": 6.0,
        "readiness_score": 45.0,
        "github_url": "https://github.com/manoj-kumar-jdev",
        "linkedin_url": "https://linkedin.com/in/manoj-kumar-java",
        "current_ctc": "12 LPA",
        "expected_ctc": "20 LPA",
        "notice_period": "90 days",
        "working_status": "Currently working",
        "preferred_location": "Pune, Mumbai",
        "resume_overall_score": 45,
        "resume_analysis": {
            "overall_score": 45,
            "summary": "Long single-company tenure on Java/Spring; minimal cloud or modern stack exposure for this JD.",
            "sub_scores": {"skills_score": 50, "experience_score": 55, "education_score": 50, "value_add_score": 25},
            "analytics": {
                "skill_count": 5, "avg_tenure_months": 65, "longest_tenure_months": 65,
                "employment_gap_months": 0, "job_count": 1,
                "education_level": "BACHELORS", "top_domain": "Backend",
                # 65mo service (Infosys)
                "product_experience_years": 0.0, "service_experience_years": 5.4,
                "gcc_experience_years": 0.0, "startup_experience_years": 0.0,
                "dominant_company_type": "SERVICE",
            },
            "value_add_items": [
                {"category": "ACHIEVEMENT", "description": "Maintained a Spring Boot microservices platform at Infosys."},
            ],
        },
        "linkedin_cross_check": {
            "match_score": 42,
            "consistent": False,
            "summary": "Significant inconsistency: resume lists a senior role missing on LinkedIn and dates conflict by ~1 year.",
            "mismatches": [
                {"type": "missing_on_linkedin", "company": "Infosys", "details": "Resume claims 'Tech Lead' from 2022 onward; LinkedIn shows the role remains 'Senior Developer'."},
                {"type": "date_mismatch", "company": "Infosys", "details": "Resume start: Jun 2019. LinkedIn start: Jun 2020 — a one-year discrepancy."},
            ],
        },
        "skills": [
            ("Java", "EXPERT", 6.0),
            ("Spring Boot", "ADVANCED", 5.0),
            ("PostgreSQL", "ADVANCED", 4.0),
            ("Docker", "INTERMEDIATE", 2.0),
            ("AWS", "INTERMEDIATE", 2.0),
        ],
        "experiences": [
            {"company": "Infosys", "title": "Java Developer", "start_date": "2019-06", "end_date": None, "duration_months": 65, "is_current": True, "domain": "IT Services", "company_type": "SERVICE"},
        ],
        "interview_score": 55.0,
        "l1_status": "FAILED",
    },
]


def _l1_status(score: float) -> str:
    return "PASSED" if score >= 60 else "FAILED"


def _recommendation(score: float) -> str:
    if score >= 70:
        return "PROCEED_TO_L2"
    if score >= 55:
        return "MANUAL_REVIEW"
    return "REJECT"


# Realistic two-question Q&A per candidate, tuned to their domain + interview tier.
# Keyed by email so each candidate gets domain-appropriate content.
INTERVIEW_QA: dict[str, dict] = {
    "arjun.verma@example.com": {
        "questions": [
            {
                "q_id": "q1", "category": "TECHNICAL", "difficulty": "HARD",
                "question": "Walk me through how you would design an LLM-powered semantic search system handling 40 million monthly requests. What would your architecture look like end-to-end?",
                "expected_answer_points": ["embedding model choice", "vector store", "caching layer", "latency budget"],
                "targets_skill": "LLM",
            },
            {
                "q_id": "q2", "category": "TECHNICAL", "difficulty": "HARD",
                "question": "Tell me about a production incident you led the response to. What was the root cause and what did you change after?",
                "expected_answer_points": ["concrete incident", "RCA", "preventative measure", "team coordination"],
                "targets_skill": "LEADERSHIP",
            },
        ],
        "answers": [
            {"quality": "CORRECT", "score": 92, "text": "Sure. I'd start with sentence-transformer embeddings — we used the gte-large model in production at Razorpay. Embeddings go into a managed vector store, in our case Vertex AI Matching Engine. There's a Redis cache in front for the top 5% of queries that account for 60% of traffic. The retrieval path uses approximate nearest neighbor with ef_search tuned to 200, giving us p95 around 60ms. We post-rerank the top-50 with a cross-encoder when the user's intent looks ambiguous. Telemetry to Prometheus and a feedback loop where click-through events update a learning-to-rank layer offline once a day."},
            {"quality": "CORRECT", "score": 88, "text": "We had a payment-link generation outage where new links returned 502 for about 40 minutes. Root cause was a connection pool exhaustion on our Aurora reader after a deploy doubled the per-request DB hits. I led the response — paused the rollout, escalated to AWS, and we drained traffic to the previous version. After the incident I added connection-pool gauges to our Grafana dashboards, instituted a soft cap on per-request DB calls via a middleware, and we wrote a runbook for the on-call team. Hasn't recurred."},
        ],
    },
    "priya.sharma@example.com": {
        "questions": [
            {
                "q_id": "q1", "category": "TECHNICAL", "difficulty": "MEDIUM",
                "question": "You rewrote the Zomato checkout in FastAPI and cut p95 latency by 38%. Walk through the changes that drove that improvement.",
                "expected_answer_points": ["async I/O", "specific bottleneck", "before/after numbers", "rollback strategy"],
                "targets_skill": "FastAPI",
            },
            {
                "q_id": "q2", "category": "BEHAVIORAL", "difficulty": "MEDIUM",
                "question": "How do you handle a disagreement with a senior engineer on an architectural decision?",
                "expected_answer_points": ["concrete example", "communication", "escalation path", "outcome"],
                "targets_skill": "COMMUNICATION",
            },
        ],
        "answers": [
            {"quality": "CORRECT", "score": 80, "text": "The previous Django/DRF endpoint was synchronously waiting on three external API calls — restaurant menu, pricing service, and inventory. I moved it to FastAPI with asyncio.gather across those three calls, which gave us about 220ms back. We also added an in-process LRU for the pricing data with a 30-second TTL since pricing changes rarely. p95 went from 720ms to 445ms. Rollout was behind a 5% canary for two days, then full."},
            {"quality": "PARTIAL", "score": 65, "text": "Recently we disagreed on whether to use GraphQL or REST for a new partner-facing API. I felt GraphQL would over-complicate it. I wrote a one-pager outlining the tradeoffs for our specific use case and we discussed it with the architect. We ended up with REST but with a more flexible filtering interface."},
        ],
    },
    "rahul.iyer@example.com": {
        "questions": [
            {
                "q_id": "q1", "category": "TECHNICAL", "difficulty": "MEDIUM",
                "question": "Walk me through how you'd structure a FastAPI service that handles 1M requests per day. What about deployment and scaling?",
                "expected_answer_points": ["async patterns", "DB connection pooling", "horizontal scaling", "monitoring"],
                "targets_skill": "FastAPI",
            },
            {
                "q_id": "q2", "category": "TECHNICAL", "difficulty": "MEDIUM",
                "question": "How would you debug a sudden 99th-percentile latency spike in a production API?",
                "expected_answer_points": ["systematic approach", "tools used", "common causes", "communication"],
                "targets_skill": "DEBUGGING",
            },
        ],
        "answers": [
            {"quality": "PARTIAL", "score": 72, "text": "Our Swiggy partner API runs on FastAPI behind nginx. We have 4 uvicorn workers per pod, 6 pods on EKS. DB connection pool is set to 10 per worker with overflow at 5. We use asyncpg with PostgreSQL. For scaling we use HPA based on CPU. Monitoring with Datadog. To handle bursts we have rate-limiting per partner using Redis as the counter store. I'd want to add more around request tracing — we only have basic spans right now."},
            {"quality": "PARTIAL", "score": 68, "text": "First I'd check our APM dashboard to see if it's specific endpoints. Then look at DB query times — usually it's a query plan flip after a stats update. I'd also check if any downstream service is slow. We had one case where a vendor's webhook was retrying through us and that pushed up tail latency. Fixed with a circuit breaker."},
        ],
    },
    "sneha.reddy@example.com": {
        "questions": [
            {
                "q_id": "q1", "category": "TECHNICAL", "difficulty": "MEDIUM",
                "question": "Describe the architecture of your component library at Myntra. How did you handle theming and accessibility?",
                "expected_answer_points": ["Storybook", "TypeScript types", "a11y testing", "theming approach"],
                "targets_skill": "React",
            },
            {
                "q_id": "q2", "category": "TECHNICAL", "difficulty": "MEDIUM",
                "question": "How would you optimize a React app that's rendering slowly on a list page with 500+ items?",
                "expected_answer_points": ["virtualization", "memoization", "code splitting", "DevTools profiling"],
                "targets_skill": "React",
            },
        ],
        "answers": [
            {"quality": "CORRECT", "score": 75, "text": "We built it on top of Radix primitives with our own design tokens. Each component is fully typed in TypeScript with strict generic constraints. Theming is done via CSS variables — light/dark and a high-contrast mode. For accessibility we run axe-core in CI for every Storybook story; we caught around 40 issues that way before any of them shipped. The library is consumed by two product teams; we version it with changesets and ship via GitHub Packages."},
            {"quality": "PARTIAL", "score": 55, "text": "Start by profiling with React DevTools to see which components are re-rendering unnecessarily. Wrap them in React.memo if their props are stable. For a long list, react-window or react-virtual to only render visible rows. Move expensive computations to useMemo. Sometimes splitting the route with React.lazy helps initial load. I'd also check if the parent is passing new object references on every render."},
        ],
    },
    "manoj.kumar@example.com": {
        "questions": [
            {
                "q_id": "q1", "category": "TECHNICAL", "difficulty": "MEDIUM",
                "question": "How would you migrate a Spring Boot monolith to microservices? What would your approach be?",
                "expected_answer_points": ["strangler pattern", "service boundaries", "data ownership", "phased rollout"],
                "targets_skill": "Spring Boot",
            },
            {
                "q_id": "q2", "category": "TECHNICAL", "difficulty": "MEDIUM",
                "question": "Tell me about a Python or modern stack project you've recently worked on outside of Java.",
                "expected_answer_points": ["concrete project", "tech stack chosen", "what you learned"],
                "targets_skill": "VERSATILITY",
            },
        ],
        "answers": [
            {"quality": "PARTIAL", "score": 60, "text": "I would identify the bounded contexts first — usually starting with the customer-facing modules. Extract one service at a time using the strangler pattern. Database-per-service is the ideal but in practice we'd do shared DB with schemas owned per service initially. Use Spring Cloud Gateway for routing. We did this kind of migration at Infosys for a banking client."},
            {"quality": "INCORRECT", "score": 30, "text": "I haven't done a lot outside of Java/Spring honestly. I've read about Python and FastAPI but haven't built anything significant. Most of my work has been on enterprise Java projects."},
        ],
    },
}


def _make_evaluation_data(c: dict, candidate_email: str) -> tuple[dict, list[dict]]:
    """Build evaluation_data + question rows for a candidate's interview."""
    qa = INTERVIEW_QA.get(candidate_email)
    score = c["interview_score"]
    l1 = _l1_status(score)
    rec = _recommendation(score)
    questions = qa["questions"] if qa else []
    answers = qa["answers"] if qa else []
    answer_validation = [
        {
            "question": q["question"],
            "answer": a["text"],
            "answer_quality": a["quality"],
            "score": a["score"],
        }
        for q, a in zip(questions, answers)
    ]
    eval_data = {
        "overall_score": score,
        "l1_status": l1,
        "recommendation": rec,
        "evaluation": {
            "technical": {"score": min(100, score + 2), "assessment": "Solid technical foundation"},
            "behavioral": {"score": max(0, score - 2), "assessment": "Good communication"},
            "experience": {"score": score, "assessment": "Relevant experience"},
        },
        "answer_validation": answer_validation,
    }
    return eval_data, questions


def _build_transcript(c: dict, candidate_email: str) -> str:
    """Build a readable full transcript from the per-question Q&A."""
    qa = INTERVIEW_QA.get(candidate_email)
    if not qa:
        return ""
    parts = []
    for i, (q, a) in enumerate(zip(qa["questions"], qa["answers"]), start=1):
        parts.append(f"[Interviewer] Q{i}: {q['question']}")
        parts.append(f"[{c['full_name']}] {a['text']}")
    return "\n\n".join(parts)


async def get_or_create_skill(db, name: str, category: str) -> SkillTaxonomy:
    existing = await db.execute(
        select(SkillTaxonomy).where(func.lower(SkillTaxonomy.standard_name) == name.lower())
    )
    skill = existing.scalar_one_or_none()
    if skill:
        return skill
    skill = SkillTaxonomy(standard_name=name, category=category)
    db.add(skill)
    await db.flush()
    return skill


async def seed():
    async with async_session_factory() as db:
        # 1. Ensure all skills exist in taxonomy
        for name, cat in SKILL_CATALOG.items():
            await get_or_create_skill(db, name, cat)
        await db.commit()

        # 2. Create candidates
        year = datetime.now().year
        for idx, c in enumerate(CANDIDATES, start=1):
            ref = f"SR-{year}-{90000 + idx}"

            # Skip if already exists
            existing = await db.execute(
                select(CandidateMain).where(CandidateMain.email == c["email"])
            )
            if existing.scalar_one_or_none():
                print(f"  ↷ {c['full_name']} ({c['email']}) already exists — skipping")
                continue

            main = CandidateMain(
                candidate_ref=ref,
                full_name=c["full_name"],
                email=c["email"],
                phone=c["phone"],
                current_title=c["current_title"],
                primary_domain=c["primary_domain"],
                location=c["location"],
                target_role=c["target_role"],
                total_experience_years=c["total_experience_years"],
                readiness_score=c["readiness_score"],
                # New fields surfaced on the hiring-manager UI
                github_url=c.get("github_url"),
                linkedin_url=c.get("linkedin_url"),
                current_ctc=c.get("current_ctc"),
                expected_ctc=c.get("expected_ctc"),
                notice_period=c.get("notice_period"),
                working_status=c.get("working_status"),
                preferred_location=c.get("preferred_location"),
                resume_overall_score=c.get("resume_overall_score"),
                resume_analysis=c.get("resume_analysis"),
                linkedin_cross_check=c.get("linkedin_cross_check"),
                status="VERIFIED",
                verification_status="VERIFIED",
                talent_pool_entry_date=datetime.now(timezone.utc),
            )
            db.add(main)
            await db.flush()

            # Skills
            for skill_name, prof, yrs in c["skills"]:
                taxonomy = await get_or_create_skill(db, skill_name, SKILL_CATALOG.get(skill_name, "GENERAL"))
                db.add(CandidateSkill(
                    candidate_id=main.id,
                    skill_id=taxonomy.id,
                    proficiency=prof,
                    years_experience=yrs,
                    is_implied=False,
                    confidence=0.95,
                ))

            # Experiences
            for exp in c["experiences"]:
                db.add(CandidateExperience(
                    candidate_id=main.id,
                    company=exp["company"],
                    title=exp["title"],
                    start_date=exp["start_date"],
                    end_date=exp["end_date"],
                    duration_months=exp["duration_months"],
                    is_current=exp["is_current"],
                    domain=exp["domain"],
                    company_type=exp.get("company_type", "OTHER"),
                ))

            # Education (one row each — enough for the UI)
            db.add(CandidateEducation(
                candidate_id=main.id,
                institution="IIT Bombay" if idx % 2 else "BITS Pilani",
                degree="B.Tech",
                field="Computer Science",
                graduation_year=2020 - int(c["total_experience_years"]),
            ))

            # Interview (scored) — use the same thresholds as agent5
            score = c["interview_score"]
            l1 = _l1_status(score)
            rec = _recommendation(score)
            interview_id = uuid.uuid4()
            eval_data, qa_questions = _make_evaluation_data(c, c["email"])
            transcript = _build_transcript(c, c["email"])
            db.add(Interview(
                id=interview_id,
                interview_ref=f"INT-{ref[-5:]}",
                candidate_id=main.id,
                interview_type="L1_SCREENING",
                status="SCORED",
                transcript=transcript,
                video_url=PLACEHOLDER_INTERVIEW_VIDEO_URL,
                overall_score=score,
                l1_status=l1,
                recommendation=rec,
                evaluation_data=eval_data,
            ))

            # Per-question rows so the Questions tab + per-q answers light up
            for q, av in zip(qa_questions, eval_data.get("answer_validation", [])):
                db.add(InterviewQuestion(
                    interview_id=interview_id,
                    question_ref=q.get("q_id", "q1"),
                    category=q.get("category", "TECHNICAL"),
                    question_text=q["question"],
                    targets_skill=q.get("targets_skill", ""),
                    difficulty=q.get("difficulty", "MEDIUM"),
                    expected_answer_points=q.get("expected_answer_points", []),
                    time_estimate_mins=q.get("time_estimate_mins", 5),
                    answer_quality=av.get("answer_quality"),
                    answer_score=av.get("score"),
                ))

            print(f"  ✓ {c['full_name']:20s}  {c['current_title']:30s}  {c['total_experience_years']}y  score={c['interview_score']}")

        await db.commit()


def main():
    print("Seeding 5 test candidates against the Full Stack / AI Development JD...\n")
    asyncio.run(seed())
    print("\nDone. Open the hiring manager search page and paste the JD to test ranking.")


if __name__ == "__main__":
    main()
