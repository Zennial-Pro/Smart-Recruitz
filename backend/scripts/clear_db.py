"""Standalone script to truncate all candidate/interview/task tables.

Usage:
    cd backend && .venv/bin/python scripts/clear_db.py
    cd backend && .venv/bin/python scripts/clear_db.py --yes   # skip confirmation
"""

import asyncio
import sys
from pathlib import Path

# Make `app` importable when run directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text  # noqa: E402

from app.db.session import async_session_factory  # noqa: E402

TABLES_TO_CLEAR = [
    "background_tasks",
    "candidate_educations",
    "candidate_experiences",
    "candidate_skills",
    "candidates_main",
    "candidates_staging",
    "interview_questions",
    "interviews",
    "uploaded_documents",
    "verifications",
]

PRESERVED = ["alembic_version", "skill_taxonomy"]


async def clear() -> None:
    async with async_session_factory() as session:
        truncate_sql = "TRUNCATE TABLE " + ", ".join(TABLES_TO_CLEAR) + " CASCADE"
        await session.execute(text(truncate_sql))
        await session.commit()


def main() -> None:
    skip_confirm = "--yes" in sys.argv or "-y" in sys.argv

    print("Tables to TRUNCATE (CASCADE):")
    for t in TABLES_TO_CLEAR:
        print(f"  - {t}")
    print("\nPreserved (untouched):")
    for t in PRESERVED:
        print(f"  - {t}")

    if not skip_confirm:
        ans = input("\nProceed? [y/N] ").strip().lower()
        if ans not in ("y", "yes"):
            print("Aborted.")
            return

    asyncio.run(clear())
    print("\n✓ Database cleared.")


if __name__ == "__main__":
    main()
