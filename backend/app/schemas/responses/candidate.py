"""Response schemas for candidate and task endpoints."""

from datetime import datetime

from pydantic import BaseModel


class CandidateRegisteredResponse(BaseModel):
    candidate_ref: str
    status: str


class TaskCreatedResponse(BaseModel):
    task_id: str


class VoiceCallInitiatedResponse(BaseModel):
    interview_ref: str
    call_id: str
    status: str


class InterviewStatusResponse(BaseModel):
    interview_ref: str
    status: str
    call_status: str | None = None
    overall_score: float | None = None
    l1_status: str | None = None
    recommendation: str | None = None
    # Full Agent 5 scoring blob (evaluation + answer_validation), present once SCORED.
    evaluation: dict | None = None


class TaskStatusResponse(BaseModel):
    id: str
    task_type: str
    reference_id: str
    status: str
    result: dict | None = None
    error_message: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
