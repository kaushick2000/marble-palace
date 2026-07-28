import uuid
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from app.api.deps import get_current_admin
from app.db.session import get_db
from app.models.visitor import HowHeard, ReasonForVisit, VisitorEntry
from app.schemas.visitor import VisitorEntryFilters, VisitorEntryListOut, VisitorEntryOut
from app.services.excel_export import build_visitor_entries_workbook

router = APIRouter(
    prefix="/admin/visitor-entries",
    tags=["admin"],
    dependencies=[Depends(get_current_admin)],
)


def _apply_filters(stmt: Select, filters: VisitorEntryFilters) -> Select:
    if filters.date_from is not None:
        stmt = stmt.where(VisitorEntry.created_at >= filters.date_from)
    if filters.date_to is not None:
        stmt = stmt.where(VisitorEntry.created_at <= filters.date_to)
    if filters.reason_for_visit is not None:
        stmt = stmt.where(VisitorEntry.reason_for_visit == filters.reason_for_visit)
    if filters.how_heard is not None:
        stmt = stmt.where(VisitorEntry.how_heard == filters.how_heard)
    return stmt


def _apply_sort(stmt: Select, filters: VisitorEntryFilters) -> Select:
    if filters.sort == "created_at_asc":
        return stmt.order_by(VisitorEntry.created_at.asc())
    return stmt.order_by(VisitorEntry.created_at.desc())


@router.get("", response_model=VisitorEntryListOut)
async def list_visitor_entries(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    reason_for_visit: ReasonForVisit | None = Query(default=None),
    how_heard: HowHeard | None = Query(default=None),
    sort: Literal["created_at_asc", "created_at_desc"] = Query(default="created_at_desc"),
    db: AsyncSession = Depends(get_db),
) -> VisitorEntryListOut:
    filters = VisitorEntryFilters(
        date_from=date_from,
        date_to=date_to,
        reason_for_visit=reason_for_visit,
        how_heard=how_heard,
        sort=sort,
    )

    base_stmt = _apply_filters(select(VisitorEntry), filters)

    count_stmt = select(func.count()).select_from(base_stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    list_stmt = _apply_sort(base_stmt, filters).limit(limit).offset(offset)
    items = (await db.execute(list_stmt)).scalars().all()

    return VisitorEntryListOut(total=total, limit=limit, offset=offset, items=items)


@router.get("/export")
async def export_visitor_entries(
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    reason_for_visit: ReasonForVisit | None = Query(default=None),
    how_heard: HowHeard | None = Query(default=None),
    sort: Literal["created_at_asc", "created_at_desc"] = Query(default="created_at_desc"),
    db: AsyncSession = Depends(get_db),
) -> Response:
    filters = VisitorEntryFilters(
        date_from=date_from,
        date_to=date_to,
        reason_for_visit=reason_for_visit,
        how_heard=how_heard,
        sort=sort,
    )

    stmt = _apply_sort(_apply_filters(select(VisitorEntry), filters), filters)
    entries = (await db.execute(stmt)).scalars().all()

    content = build_visitor_entries_workbook(entries)

    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=visitor-entries.xlsx"},
    )


@router.get("/{entry_id}", response_model=VisitorEntryOut)
async def get_visitor_entry(
    entry_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> VisitorEntry:
    entry = await db.get(VisitorEntry, entry_id)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visitor entry not found")
    return entry
