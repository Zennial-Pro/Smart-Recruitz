"""SmartRecruitz auth user — standalone accounts (hiring managers / admins).

Independent of the LMS user store; SmartRecruitz manages its own login.
"""

import uuid

from sqlalchemy import Boolean, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin


class RecruitUser(TimestampMixin, Base):
    __tablename__ = "lms_recruit_users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # hiring_manager | admin
    role: Mapped[str] = mapped_column(
        String(30), nullable=False, default="hiring_manager", server_default="hiring_manager"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
