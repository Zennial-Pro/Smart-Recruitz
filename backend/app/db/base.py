"""SQLAlchemy declarative base with naming conventions."""

import uuid

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass

# Consistent constraint naming for Alembic autogenerate
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    # SmartRecruitz tables live in the LMS `application` schema (shared `lms` DB),
    # named with the lms_recruit_ prefix to match LMS conventions.
    metadata = MetaData(schema="application", naming_convention=convention)
