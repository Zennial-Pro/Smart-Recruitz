"""Task status polling endpoint."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.repositories.task_repository import get_task
from app.schemas.responses.candidate import TaskStatusResponse

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> TaskStatusResponse:
    task = await get_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskStatusResponse(
        id=str(task.id),
        task_type=task.task_type,
        reference_id=task.reference_id,
        status=task.status,
        result=task.result,
        error_message=task.error_message,
        created_at=task.created_at,
        started_at=task.started_at,
        completed_at=task.completed_at,
    )
