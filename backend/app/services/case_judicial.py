"""Helpers dossier judiciaire — délais de recours à partir de la notification."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone


def default_appeal_days(degree: str | None) -> int:
    if degree == "refere":
        return 15
    return 30


def compute_appeal_deadline(
    notification: datetime | None,
    days: int | None,
    degree: str | None = None,
) -> datetime | None:
    if not notification:
        return None
    d = days if days and days > 0 else default_appeal_days(degree)
    nt = notification
    if nt.tzinfo is None:
        nt = nt.replace(tzinfo=timezone.utc)
    return nt + timedelta(days=d)
