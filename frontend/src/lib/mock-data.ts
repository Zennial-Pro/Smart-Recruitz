/** Mock data for testing the full onboarding flow without a backend. */

export const mockResumeParseResult = {
  parse_status: "SUCCESS",
  confidence_score: 0.94,
  full_name: "Rahul Kumar",
  email: "rahul.kumar@example.com",
  phone: "+91 98765 43210",
  current_title: "Senior Software Engineer",
  total_experience_years: 6.5,
  primary_domain: "FinTech",
  experience: [
    {
      company: "Razorpay",
      title: "Senior Software Engineer",
      domain: "FinTech",
      duration_months: 36,
      start_date: "2021-06",
      end_date: null,
      is_current: true,
      responsibilities: [
        "Led payments microservices handling 10M+ transactions/day",
        "Designed event-driven architecture using Kafka",
        "Mentored team of 4 junior engineers",
      ],
    },
    {
      company: "Flipkart",
      title: "Software Engineer",
      domain: "E-Commerce",
      duration_months: 30,
      start_date: "2019-01",
      end_date: "2021-06",
      is_current: false,
      responsibilities: [
        "Built inventory management system in Python",
        "Optimized database queries reducing latency by 40%",
      ],
    },
  ],
  education: [
    {
      institution: "IIT Bombay",
      degree: "B.Tech",
      field: "Computer Science",
      graduation_year: 2018,
    },
  ],
  skills_normalized: [
    { standard_name: "Python", proficiency: "EXPERT", evidence: "6 years, primary language" },
    { standard_name: "System Design", proficiency: "ADVANCED", evidence: "Designed microservices at scale" },
    { standard_name: "PostgreSQL", proficiency: "ADVANCED", evidence: "Query optimization, schema design" },
    { standard_name: "Kafka", proficiency: "ADVANCED", evidence: "Event-driven architecture at Razorpay" },
    { standard_name: "Docker", proficiency: "INTERMEDIATE", evidence: "Containerized services" },
    { standard_name: "Kubernetes", proficiency: "INTERMEDIATE", evidence: "Managed deployments" },
    { standard_name: "React", proficiency: "INTERMEDIATE", evidence: "Internal dashboards" },
    { standard_name: "Redis", proficiency: "ADVANCED", evidence: "Caching layer for payments" },
    { standard_name: "AWS", proficiency: "INTERMEDIATE", evidence: "EC2, S3, Lambda" },
    { standard_name: "FastAPI", proficiency: "EXPERT", evidence: "Built multiple production APIs" },
  ],
  domain_wise_experience: [
    { domain: "FinTech", years: 3 },
    { domain: "E-Commerce", years: 2.5 },
  ],
};

export const mockDuplicateResult = {
  is_duplicate: false,
  confidence: 0.12,
  recommendation: "UNIQUE",
};

export const mockVerificationResult = {
  status: "VERIFIED",
  confidence_score: 96,
  extracted_data: {
    full_name: "Rahul Kumar",
    date_of_birth: "1996-03-15",
    id_number: "XXXX-XXXX-4521",
  },
  data_match: {
    name: { match: true, score: 100 },
    dob: { match: true, score: 100 },
  },
  document_authenticity: {
    is_authentic: true,
    fraud_indicators: [],
  },
};

export const mockQuestions = {
  interview_ref: "INT-2024-00789",
  questions: [
    {
      q_id: "Q-001",
      category: "EXPERIENCE_VERIFICATION",
      question: "You mentioned handling 10M+ transactions per day at Razorpay. Walk me through the architecture of your payments microservices.",
      targets_skill: "System Design",
      difficulty: "SENIOR",
      expected_answer_points: [
        "Load balancing strategy (round-robin, consistent hashing)",
        "Database sharding or partitioning approach",
        "Kafka event streaming for async processing",
        "Redis caching for hot payment paths",
        "Idempotency handling for payment retries",
      ],
      time_estimate_mins: 5,
    },
    {
      q_id: "Q-002",
      category: "TECHNICAL",
      question: "How would you design a rate limiter for an API gateway? What data structures and algorithms would you use?",
      targets_skill: "System Design",
      difficulty: "SENIOR",
      expected_answer_points: [
        "Token bucket or sliding window algorithm",
        "Redis for distributed state",
        "Per-user and per-endpoint limits",
        "Graceful degradation under load",
      ],
      time_estimate_mins: 5,
    },
    {
      q_id: "Q-003",
      category: "TECHNICAL",
      question: "Explain Python's GIL. How does it affect your async FastAPI services? What strategies do you use for CPU-bound tasks?",
      targets_skill: "Python",
      difficulty: "SENIOR",
      expected_answer_points: [
        "GIL prevents true parallelism for CPU-bound threads",
        "asyncio for I/O-bound concurrency",
        "multiprocessing or ProcessPoolExecutor for CPU-bound",
        "Celery/ARQ for background task offloading",
      ],
      time_estimate_mins: 4,
    },
    {
      q_id: "Q-004",
      category: "EXPERIENCE_VERIFICATION",
      question: "At Flipkart, you optimized database queries and reduced latency by 40%. What specific techniques did you apply?",
      targets_skill: "PostgreSQL",
      difficulty: "MID",
      expected_answer_points: [
        "Query EXPLAIN analysis",
        "Index optimization (composite, partial, covering)",
        "N+1 query elimination",
        "Connection pooling",
      ],
      time_estimate_mins: 4,
    },
    {
      q_id: "Q-005",
      category: "BEHAVIORAL",
      question: "Tell me about a time you had to mentor a junior engineer through a challenging technical problem. How did you approach it?",
      targets_skill: "Leadership",
      difficulty: "MID",
      expected_answer_points: [
        "Specific example with context",
        "Teaching approach (pair programming, code review)",
        "Outcome and growth of the mentee",
        "Lessons learned",
      ],
      time_estimate_mins: 3,
    },
    {
      q_id: "Q-006",
      category: "TECHNICAL",
      question: "How do you handle distributed transactions across microservices? What patterns do you prefer and why?",
      targets_skill: "System Design",
      difficulty: "LEAD",
      expected_answer_points: [
        "Saga pattern (choreography vs orchestration)",
        "Eventual consistency trade-offs",
        "Compensation/rollback strategies",
        "Outbox pattern for reliable event publishing",
      ],
      time_estimate_mins: 5,
    },
  ],
  interviewer_guide: {
    focus_areas: [
      "Verify payments microservices experience depth",
      "Assess system design maturity",
      "Python expertise beyond basic usage",
    ],
    red_flags: [
      "Cannot explain architecture details of own projects",
      "No awareness of distributed systems trade-offs",
    ],
  },
};

export const mockScoringResult = {
  overall_score: 78,
  l1_status: "PASSED",
  recommendation: "PROCEED_TO_L2",
  readiness_level: "INTERVIEW_READY",
  evaluation: {
    technical_knowledge: {
      score: 82,
      assessment: "Strong Python and system design fundamentals. Good understanding of distributed systems.",
    },
    communication: {
      score: 75,
      assessment: "Clear and structured responses. Could provide more concrete examples.",
    },
    problem_solving: {
      score: 80,
      assessment: "Systematic approach to problem decomposition. Good trade-off analysis.",
    },
    experience_depth: {
      score: 74,
      assessment: "Solid FinTech experience. Could elaborate more on specific metrics and outcomes.",
    },
  },
  answer_validation: [
    { question: "Payments microservices architecture", answer_quality: "CORRECT", score: 90 },
    { question: "Rate limiter design", answer_quality: "CORRECT", score: 85 },
    { question: "Python GIL explanation", answer_quality: "CORRECT", score: 88 },
    { question: "Database query optimization", answer_quality: "PARTIAL", score: 70 },
    { question: "Mentoring experience", answer_quality: "CORRECT", score: 75 },
    { question: "Distributed transactions", answer_quality: "PARTIAL", score: 65 },
  ],
};

/** Simulate an API delay */
export function mockDelay(ms: number = 2000): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
