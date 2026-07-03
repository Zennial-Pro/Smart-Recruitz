"""Internal Pydantic models for agent output validation."""

from pydantic import BaseModel, Field, field_validator


# ── Agent 1: Resume Parser ────────────────────────────────────────────────────

class SkillItem(BaseModel):
    standard_name: str
    proficiency: str  # BEGINNER | INTERMEDIATE | ADVANCED | EXPERT
    years_experience: float = 0.0
    evidence: str = ""


class ExperienceItem(BaseModel):
    company: str
    title: str
    domain: str = ""
    start_date: str = ""
    end_date: str = ""
    duration_months: int = 0
    is_current: bool = False
    # PRODUCT | SERVICE | GCC | STARTUP | OTHER — classified by Agent 1 from the company name
    company_type: str = "OTHER"
    responsibilities: list[str] = Field(default_factory=list)


class EducationItem(BaseModel):
    institution: str
    degree: str
    field: str | None = ""
    graduation_year: int | None = None
    start_date: str = ""
    end_date: str = ""

    @field_validator("field", mode="before")
    @classmethod
    def coerce_field(cls, v: object) -> str:
        return v if isinstance(v, str) else ""


class ResumeSubScores(BaseModel):
    skills_score: int = 0
    experience_score: int = 0
    education_score: int = 0
    value_add_score: int = 0


class ResumeAnalytics(BaseModel):
    skill_count: int = 0
    avg_tenure_months: int = 0
    longest_tenure_months: int = 0
    employment_gap_months: int = 0
    job_count: int = 0
    education_level: str = "OTHER"
    top_domain: str = ""
    # Years split by company orientation — sum may differ slightly from
    # total_experience_years if some roles are classified OTHER.
    product_experience_years: float = 0.0
    service_experience_years: float = 0.0
    gcc_experience_years: float = 0.0
    startup_experience_years: float = 0.0
    dominant_company_type: str = "OTHER"  # PRODUCT | SERVICE | GCC | STARTUP | OTHER


class ValueAddItem(BaseModel):
    category: str  # ACHIEVEMENT | CERTIFICATION | OPEN_SOURCE | LEADERSHIP | PUBLICATION | AWARD | SIDE_PROJECT
    description: str


class ResumeAnalysis(BaseModel):
    overall_score: int = 0
    summary: str = ""
    sub_scores: ResumeSubScores = Field(default_factory=ResumeSubScores)
    analytics: ResumeAnalytics = Field(default_factory=ResumeAnalytics)
    value_add_items: list[ValueAddItem] = Field(default_factory=list)


class ResumeParseOutput(BaseModel):
    full_name: str
    email: str
    phone: str
    current_title: str = ""
    total_experience_years: float = 0.0
    primary_domain: str = ""
    github_url: str = ""
    linkedin_url: str = ""
    confidence_score: float = 0.0
    skills_normalized: list[SkillItem] = Field(default_factory=list)
    experience: list[ExperienceItem] = Field(default_factory=list)
    education: list[EducationItem] = Field(default_factory=list)
    analysis: ResumeAnalysis = Field(default_factory=ResumeAnalysis)


class ConsistencyMismatch(BaseModel):
    type: str  # missing_on_linkedin | missing_on_resume | date_mismatch | title_drift | company_mismatch
    company: str = ""
    details: str = ""


class ConsistencyCheckOutput(BaseModel):
    match_score: int  # 0-100
    consistent: bool
    summary: str = ""
    mismatches: list[ConsistencyMismatch] = Field(default_factory=list)


# ── JD Extraction ─────────────────────────────────────────────────────────────

class JDExtractionOutput(BaseModel):
    role_title: str = ""
    role_level: str = ""  # JUNIOR | MID | SENIOR | STAFF | PRINCIPAL | LEAD | OTHER
    domain: str = ""
    min_experience_years: float = 0.0
    mandatory_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    summary: str = ""


# ── Agent 2: Duplicate Detector ───────────────────────────────────────────────

class DuplicateCheckOutput(BaseModel):
    result: str  # UNIQUE | DUPLICATE | UNCERTAIN
    confidence: float
    matched_candidate_ref: str | None = None
    reasoning: str = ""


# ── Agent 3: ID Verifier ──────────────────────────────────────────────────────

class VerificationOutput(BaseModel):
    status: str  # VERIFIED | FAILED
    confidence_score: float
    document_type: str
    extracted_data: dict = Field(default_factory=dict)
    data_match_results: dict = Field(default_factory=dict)
    flags: list[str] = Field(default_factory=list)


# ── Agent 4: Question Generator ───────────────────────────────────────────────

class QuestionItem(BaseModel):
    q_id: str  # Q-001, Q-002, …
    category: str  # EXPERIENCE_VERIFICATION | TECHNICAL | BEHAVIORAL
    question: str
    targets_skill: str = ""
    difficulty: str = "MID"  # MID | SENIOR | LEAD
    expected_answer_points: list[str] = Field(default_factory=list)
    time_estimate_seconds: int = 120

    @field_validator("time_estimate_seconds", mode="before")
    @classmethod
    def enforce_minimum(cls, v: object) -> int:
        try:
            val = int(v)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return 120
        return max(90, val)


class QuestionsOutput(BaseModel):
    interview_ref: str
    questions: list[QuestionItem]


# ── Agent 5: Interview Scorer ─────────────────────────────────────────────────

class AnswerValidation(BaseModel):
    question: str
    answer: str = ""
    answer_quality: str  # CORRECT | PARTIAL | INCORRECT
    score: float


class CategoryEval(BaseModel):
    score: float
    assessment: str


class ScoringOutput(BaseModel):
    overall_score: float
    l1_status: str  # PASSED | FAILED
    recommendation: str  # PROCEED_TO_L2 | REJECT | MANUAL_REVIEW
    evaluation: dict[str, CategoryEval]
    answer_validation: list[AnswerValidation]
