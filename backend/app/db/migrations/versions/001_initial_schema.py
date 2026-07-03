"""Initial schema — 11 core pipeline tables.

Revision ID: 001_initial
Revises:
Create Date: 2026-03-25
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pg_trgm extension for fuzzy name matching (Agent 2)
    op.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm"')

    # 1. uploaded_documents (no FKs — referenced by others)
    op.create_table(
        "uploaded_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("content_type", sa.String(100), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("storage_path", sa.String(500), nullable=False),
        sa.Column("document_category", sa.String(30), nullable=False),
        sa.Column("uploaded_by_ref", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_uploaded_documents")),
    )

    # 2. skill_taxonomy (self-referential FK)
    op.create_table(
        "skill_taxonomy",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("standard_name", sa.String(255), nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("aliases", postgresql.JSONB(), nullable=True),
        sa.Column("parent_skill_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_skill_taxonomy")),
        sa.UniqueConstraint("standard_name", name=op.f("uq_skill_taxonomy_standard_name")),
        sa.ForeignKeyConstraint(["parent_skill_id"], ["skill_taxonomy.id"], name=op.f("fk_skill_taxonomy_parent_skill_id_skill_taxonomy"), ondelete="SET NULL"),
    )
    op.create_index(op.f("ix_skill_taxonomy_standard_name"), "skill_taxonomy", ["standard_name"])

    # 3. candidates_staging
    op.create_table(
        "candidates_staging",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("candidate_ref", sa.String(50), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(50), nullable=False),
        sa.Column("current_title", sa.String(255), nullable=True),
        sa.Column("raw_resume_data", postgresql.JSONB(), nullable=True),
        sa.Column("skills_normalized", postgresql.JSONB(), nullable=True),
        sa.Column("experience", postgresql.JSONB(), nullable=True),
        sa.Column("education", postgresql.JSONB(), nullable=True),
        sa.Column("certifications", postgresql.JSONB(), nullable=True),
        sa.Column("projects", postgresql.JSONB(), nullable=True),
        sa.Column("languages", postgresql.JSONB(), nullable=True),
        sa.Column("domain_experience", postgresql.JSONB(), nullable=True),
        sa.Column("duplicate_pre_check", postgresql.JSONB(), nullable=True),
        sa.Column("total_experience_years", sa.Float(), nullable=True),
        sa.Column("primary_domain", sa.String(100), nullable=True),
        sa.Column("parse_confidence", sa.Float(), nullable=True),
        sa.Column("resume_document_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_candidates_staging")),
        sa.UniqueConstraint("candidate_ref", name=op.f("uq_candidates_staging_candidate_ref")),
        sa.ForeignKeyConstraint(["resume_document_id"], ["uploaded_documents.id"], name=op.f("fk_candidates_staging_resume_document_id_uploaded_documents"), ondelete="SET NULL"),
    )
    op.create_index(op.f("ix_candidates_staging_candidate_ref"), "candidates_staging", ["candidate_ref"])
    op.create_index(op.f("ix_candidates_staging_email"), "candidates_staging", ["email"])
    op.create_index(op.f("ix_candidates_staging_phone"), "candidates_staging", ["phone"])

    # 4. candidates_main
    op.create_table(
        "candidates_main",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("candidate_ref", sa.String(50), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(50), nullable=False),
        sa.Column("current_title", sa.String(255), nullable=True),
        sa.Column("total_experience_years", sa.Float(), nullable=True),
        sa.Column("primary_domain", sa.String(100), nullable=True),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("target_role", sa.String(255), nullable=True),
        sa.Column("readiness_score", sa.Float(), nullable=True),
        sa.Column("verification_status", sa.String(30), nullable=False),
        sa.Column("talent_pool_entry_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("raw_profile_data", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_candidates_main")),
        sa.UniqueConstraint("candidate_ref", name=op.f("uq_candidates_main_candidate_ref")),
        sa.UniqueConstraint("email", name=op.f("uq_candidates_main_email")),
        sa.UniqueConstraint("phone", name=op.f("uq_candidates_main_phone")),
    )
    op.create_index(op.f("ix_candidates_main_candidate_ref"), "candidates_main", ["candidate_ref"])
    # pg_trgm GIN index for fuzzy name search (Agent 2)
    op.create_index(
        "ix_candidates_main_full_name_trgm",
        "candidates_main",
        ["full_name"],
        postgresql_using="gin",
        postgresql_ops={"full_name": "gin_trgm_ops"},
    )

    # 5. candidate_skills
    op.create_table(
        "candidate_skills",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("skill_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("proficiency", sa.String(20), nullable=False),
        sa.Column("years_experience", sa.Float(), nullable=True),
        sa.Column("evidence", sa.String(500), nullable=True),
        sa.Column("is_implied", sa.Boolean(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_candidate_skills")),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates_main.id"], name=op.f("fk_candidate_skills_candidate_id_candidates_main"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["skill_id"], ["skill_taxonomy.id"], name=op.f("fk_candidate_skills_skill_id_skill_taxonomy"), ondelete="CASCADE"),
    )

    # 6. candidate_experiences
    op.create_table(
        "candidate_experiences",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company", sa.String(255), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("start_date", sa.String(20), nullable=True),
        sa.Column("end_date", sa.String(20), nullable=True),
        sa.Column("duration_months", sa.Integer(), nullable=True),
        sa.Column("domain", sa.String(100), nullable=True),
        sa.Column("is_current", sa.Boolean(), nullable=False),
        sa.Column("responsibilities", postgresql.JSONB(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_candidate_experiences")),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates_main.id"], name=op.f("fk_candidate_experiences_candidate_id_candidates_main"), ondelete="CASCADE"),
    )

    # 7. candidate_educations
    op.create_table(
        "candidate_educations",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("institution", sa.String(255), nullable=False),
        sa.Column("degree", sa.String(100), nullable=False),
        sa.Column("field", sa.String(255), nullable=True),
        sa.Column("graduation_year", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_candidate_educations")),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates_main.id"], name=op.f("fk_candidate_educations_candidate_id_candidates_main"), ondelete="CASCADE"),
    )

    # 8. verifications
    op.create_table(
        "verifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("verification_ref", sa.String(50), nullable=False),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("verification_type", sa.String(20), nullable=False),
        sa.Column("document_type", sa.String(30), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("extracted_data", postgresql.JSONB(), nullable=True),
        sa.Column("data_match_results", postgresql.JSONB(), nullable=True),
        sa.Column("document_authenticity", postgresql.JSONB(), nullable=True),
        sa.Column("flags", postgresql.JSONB(), nullable=True),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_verifications")),
        sa.UniqueConstraint("verification_ref", name=op.f("uq_verifications_verification_ref")),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates_main.id"], name=op.f("fk_verifications_candidate_id_candidates_main"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["document_id"], ["uploaded_documents.id"], name=op.f("fk_verifications_document_id_uploaded_documents"), ondelete="SET NULL"),
    )
    op.create_index(op.f("ix_verifications_verification_ref"), "verifications", ["verification_ref"])

    # 9. interviews
    op.create_table(
        "interviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("interview_ref", sa.String(50), nullable=False),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("interview_type", sa.String(20), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("transcript", sa.Text(), nullable=True),
        sa.Column("overall_score", sa.Float(), nullable=True),
        sa.Column("l1_status", sa.String(20), nullable=True),
        sa.Column("recommendation", sa.String(30), nullable=True),
        sa.Column("evaluation_data", postgresql.JSONB(), nullable=True),
        sa.Column("interviewer_guide", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_interviews")),
        sa.UniqueConstraint("interview_ref", name=op.f("uq_interviews_interview_ref")),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates_main.id"], name=op.f("fk_interviews_candidate_id_candidates_main"), ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_interviews_interview_ref"), "interviews", ["interview_ref"])

    # 10. interview_questions
    op.create_table(
        "interview_questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("interview_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("question_ref", sa.String(20), nullable=False),
        sa.Column("category", sa.String(30), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("targets_skill", sa.String(100), nullable=True),
        sa.Column("targets_experience", sa.String(255), nullable=True),
        sa.Column("difficulty", sa.String(20), nullable=False),
        sa.Column("expected_answer_points", postgresql.JSONB(), nullable=True),
        sa.Column("follow_up_questions", postgresql.JSONB(), nullable=True),
        sa.Column("time_estimate_mins", sa.Integer(), nullable=True),
        sa.Column("answer_quality", sa.String(20), nullable=True),
        sa.Column("answer_score", sa.Float(), nullable=True),
        sa.Column("question_hash", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_interview_questions")),
        sa.ForeignKeyConstraint(["interview_id"], ["interviews.id"], name=op.f("fk_interview_questions_interview_id_interviews"), ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_interview_questions_question_hash"), "interview_questions", ["question_hash"])

    # 11. background_tasks
    op.create_table(
        "background_tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("task_type", sa.String(50), nullable=False),
        sa.Column("reference_id", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("result", postgresql.JSONB(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_background_tasks")),
    )
    op.create_index(op.f("ix_background_tasks_reference_id"), "background_tasks", ["reference_id"])


def downgrade() -> None:
    op.drop_table("background_tasks")
    op.drop_table("interview_questions")
    op.drop_table("interviews")
    op.drop_table("verifications")
    op.drop_table("candidate_educations")
    op.drop_table("candidate_experiences")
    op.drop_table("candidate_skills")
    op.drop_index("ix_candidates_main_full_name_trgm", table_name="candidates_main")
    op.drop_table("candidates_main")
    op.drop_table("candidates_staging")
    op.drop_table("skill_taxonomy")
    op.drop_table("uploaded_documents")
    op.execute('DROP EXTENSION IF EXISTS "pg_trgm"')
