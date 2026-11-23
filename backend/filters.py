from datetime import datetime, timezone

from fastapi import HTTPException


def date_range(date_from: datetime | None, date_to: datetime | None) -> dict:
    for value in (date_from, date_to):
        if value is not None and value.utcoffset() is None:
            raise HTTPException(422, "Las fechas requieren zona horaria, por ejemplo 2026-11-22T00:00:00Z.")
    if date_from is not None and date_to is not None and date_from > date_to:
        raise HTTPException(422, "dateFrom no puede ser posterior a dateTo.")
    result = {}
    if date_from is not None:
        result["$gte"] = date_from.astimezone(timezone.utc)
    if date_to is not None:
        result["$lte"] = date_to.astimezone(timezone.utc)
    return result
