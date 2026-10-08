"""Bangkok time formatting for customer-facing timestamps."""

from datetime import timedelta, timezone

# Thailand has no DST, so a fixed offset needs no zoneinfo data.
BANGKOK = timezone(timedelta(hours=7), "Asia/Bangkok")

# Fixed English month names; %b depends on the process locale.
_MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun",
           "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def time_view(at):
    """Display text and machine-readable ISO time of an aware datetime, in Bangkok time."""
    t = at.astimezone(BANGKOK)
    return {
        "text": f"{t.day} {_MONTHS[t.month - 1]} {t.year}, {t:%H:%M}",
        "iso": t.isoformat(timespec="seconds"),
    }
