"""Business constants, status enums, and reference prefixes."""

from enum import StrEnum


# ============================================================================
# Candidate Status Enums
# ============================================================================

class StagingStatus(StrEnum):
    PENDING = "PENDING"
    DUPLICATE_REVIEW = "DUPLICATE_REVIEW"
    AWAITING_HR_REVIEW = "AWAITING_HR_REVIEW"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"


class CandidateStatus(StrEnum):
    VERIFIED = "VERIFIED"
    IDENTITY_VERIFIED = "IDENTITY_VERIFIED"
    INTERVIEW_READY = "INTERVIEW_READY"
    TALENT_POOL = "TALENT_POOL"
    INTERVIEW_FAILED = "INTERVIEW_FAILED"
    CLOSED = "CLOSED"


class VerificationStatus(StrEnum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    MANUAL_REVIEW = "MANUAL_REVIEW"


class InterviewStatus(StrEnum):
    QUESTIONS_GENERATED = "QUESTIONS_GENERATED"
    SCHEDULED = "SCHEDULED"
    CALL_IN_PROGRESS = "CALL_IN_PROGRESS"
    COMPLETED = "COMPLETED"
    SCORED = "SCORED"
    # Outbound call failed / was not answered — candidate stays eligible, re-dial allowed.
    CALL_FAILED = "CALL_FAILED"


class CallStatus(StrEnum):
    """Lifecycle of the outbound voice-interview call (Zingaro)."""

    INITIATED = "INITIATED"
    RINGING = "RINGING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    NO_ANSWER = "NO_ANSWER"


class TaskStatus(StrEnum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class TaskType(StrEnum):
    AGENT1_RESUME_PARSE = "AGENT1_RESUME_PARSE"
    AGENT2_DUPLICATE = "AGENT2_DUPLICATE"
    AGENT3_VERIFY_IDENTITY = "AGENT3_VERIFY_IDENTITY"
    AGENT4_GENERATE_QUESTIONS = "AGENT4_GENERATE_QUESTIONS"
    AGENT5_SCORE_INTERVIEW = "AGENT5_SCORE_INTERVIEW"
    AGENT_LINKEDIN_CROSSCHECK = "AGENT_LINKEDIN_CROSSCHECK"


# ============================================================================
# Document Types
# ============================================================================

class DocumentType(StrEnum):
    AADHAAR_CARD = "AADHAAR_CARD"
    PAN_CARD = "PAN_CARD"
    PASSPORT = "PASSPORT"


class DocumentCategory(StrEnum):
    RESUME = "RESUME"
    ID_DOCUMENT = "ID_DOCUMENT"


# ============================================================================
# Skill Proficiency
# ============================================================================

class Proficiency(StrEnum):
    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"
    EXPERT = "EXPERT"


# ============================================================================
# Duplicate Detection
# ============================================================================

class DuplicateResult(StrEnum):
    UNIQUE = "UNIQUE"
    DUPLICATE = "DUPLICATE"
    UNCERTAIN = "UNCERTAIN"


class DuplicateAction(StrEnum):
    MERGE = "MERGE"
    REJECT = "REJECT"
    KEEP = "KEEP"


# ============================================================================
# Interview
# ============================================================================

class InterviewType(StrEnum):
    L1_SCREENING = "L1_SCREENING"


class L1Status(StrEnum):
    PASSED = "PASSED"
    FAILED = "FAILED"


class Recommendation(StrEnum):
    PROCEED_TO_L2 = "PROCEED_TO_L2"
    REJECT = "REJECT"
    MANUAL_REVIEW = "MANUAL_REVIEW"


class QuestionCategory(StrEnum):
    EXPERIENCE_VERIFICATION = "EXPERIENCE_VERIFICATION"
    TECHNICAL = "TECHNICAL"
    BEHAVIORAL = "BEHAVIORAL"


class AnswerQuality(StrEnum):
    CORRECT = "CORRECT"
    PARTIAL = "PARTIAL"
    INCORRECT = "INCORRECT"


class Difficulty(StrEnum):
    MID = "MID"
    SENIOR = "SENIOR"
    LEAD = "LEAD"


# ============================================================================
# Reference Prefixes
# ============================================================================

CANDIDATE_REF_PREFIX = "SR"
VERIFICATION_REF_PREFIX = "VER"
INTERVIEW_REF_PREFIX = "INT"

# ============================================================================
# Business Rules
# ============================================================================

DUPLICATE_THRESHOLD = 0.75
INTERVIEW_PASS_SCORE = 60
INTERVIEW_RETRY_DAYS = 30
RESUME_MAX_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
ID_DOC_MAX_SIZE_BYTES = 5 * 1024 * 1024   # 5 MB
PARSE_CONFIDENCE_MIN = 0.7
DEFAULT_QUESTION_COUNT = 12
