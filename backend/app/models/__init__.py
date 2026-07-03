"""SQLAlchemy models — import all for Alembic autogenerate discovery."""

from app.models.background_task import BackgroundTask
from app.models.candidate_education import CandidateEducation
from app.models.candidate_experience import CandidateExperience
from app.models.candidate_main import CandidateMain
from app.models.candidate_skill import CandidateSkill
from app.models.candidate_staging import CandidateStaging
from app.models.interview import Interview
from app.models.interview_question import InterviewQuestion
from app.models.recruit_user import RecruitUser
from app.models.skill_taxonomy import SkillTaxonomy
from app.models.uploaded_document import UploadedDocument
from app.models.verification import Verification

__all__ = [
    "BackgroundTask",
    "CandidateEducation",
    "CandidateExperience",
    "CandidateMain",
    "CandidateSkill",
    "CandidateStaging",
    "Interview",
    "InterviewQuestion",
    "RecruitUser",
    "SkillTaxonomy",
    "UploadedDocument",
    "Verification",
]
