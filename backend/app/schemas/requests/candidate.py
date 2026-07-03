"""Request schemas for candidate endpoints."""

from pydantic import BaseModel, EmailStr, field_validator


class RegisterCandidateRequest(BaseModel):
    full_name: str
    email: EmailStr
    phone: str
    target_role: str | None = None
    current_ctc: str | None = None
    expected_ctc: str | None = None
    notice_period: str | None = None
    working_status: str | None = None
    location: str | None = None
    preferred_location: str | None = None

    @field_validator("full_name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("full_name must be at least 2 characters")
        return v

    @field_validator("phone")
    @classmethod
    def phone_digits(cls, v: str) -> str:
        digits = v.replace("+", "").replace(" ", "").replace("-", "")
        if not digits.isdigit() or not (10 <= len(digits) <= 15):
            raise ValueError("phone must be 10–15 digits")
        return v


class ConfirmResumeRequest(BaseModel):
    candidate_ref: str


class ResolveDuplicateRequest(BaseModel):
    candidate_ref: str
    action: str  # MERGE | REJECT | KEEP


class ScoreInterviewRequest(BaseModel):
    candidate_ref: str
    interview_ref: str
    transcript: str


class InitiateCallRequest(BaseModel):
    candidate_ref: str
    interview_ref: str
