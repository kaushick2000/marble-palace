from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.visitor import VisitorEntry
from app.schemas.visitor import VisitorEntryCreate, VisitorEntryOut

router = APIRouter(tags=["public"])


@router.post(
    "/visitor-entries",
    response_model=VisitorEntryOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_visitor_entry(
    payload: VisitorEntryCreate,
    db: AsyncSession = Depends(get_db),
) -> VisitorEntry:
    entry = VisitorEntry(**payload.model_dump())
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry
