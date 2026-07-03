"""CRUD operations for BackgroundTask."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.background_task import BackgroundTask


async def create_task(
    db: AsyncSession, task_type: str, reference_id: str
) -> BackgroundTask:
    task = BackgroundTask(
        task_type=task_type,
        reference_id=reference_id,
        status="QUEUED",
    )
    db.add(task)
    await db.flush()
    await db.refresh(task)
    return task


async def get_task(db: AsyncSession, task_id: str) -> BackgroundTask | None:
    result = await db.execute(
        select(BackgroundTask).where(BackgroundTask.id == task_id)
    )
    return result.scalar_one_or_none()


async def mark_processing(db: AsyncSession, task_id: str) -> None:
    task = await get_task(db, task_id)
    if task:
        task.status = "PROCESSING"
        task.started_at = datetime.now(UTC)
        await db.flush()


async def mark_completed(db: AsyncSession, task_id: str, result: dict) -> None:
    task = await get_task(db, task_id)
    if task:
        task.status = "COMPLETED"
        task.result = result
        task.completed_at = datetime.now(UTC)
        await db.flush()


async def mark_failed(db: AsyncSession, task_id: str, error: str) -> None:
    task = await get_task(db, task_id)
    if task:
        task.status = "FAILED"
        task.error_message = error
        task.completed_at = datetime.now(UTC)
        await db.flush()
