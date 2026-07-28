import io
from collections.abc import Sequence

from openpyxl import Workbook

from app.models.visitor import VisitorEntry

COLUMNS: list[tuple[str, str]] = [
    ("how_heard", "How Heard"),
    ("first_name", "First Name"),
    ("last_name", "Last Name"),
    ("phone_number", "Phone Number"),
    ("email", "Email"),
    ("reason_for_visit", "Reason For Visit"),
    ("created_at", "Created At"),
]


def build_visitor_entries_workbook(entries: Sequence[VisitorEntry]) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Visitor Entries"

    ws.append([header for _, header in COLUMNS])

    for entry in entries:
        row = []
        for attr, _ in COLUMNS:
            value = getattr(entry, attr)
            if hasattr(value, "value"):  # enum
                value = value.value
            elif hasattr(value, "isoformat"):  # datetime
                value = value.isoformat()
            row.append(value)
        ws.append(row)

    for column_cells in ws.columns:
        length = max(len(str(cell.value)) if cell.value is not None else 0 for cell in column_cells)
        ws.column_dimensions[column_cells[0].column_letter].width = min(max(length + 2, 12), 40)

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()
