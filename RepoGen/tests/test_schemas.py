from datetime import date
import pytest
from pydantic import ValidationError
from repogen.schemas import EventInfo


def make(**kw):
    base = dict(
        event_name="Tech Fest", organizer="CSE Dept", event_date=date(2026, 10, 13),
        venue="Auditorium", participants=120, description="A one-day technical fest.",
    )
    base.update(kw)
    return EventInfo(**base)


def test_day_is_computed():
    assert make().day == "Tuesday"


def test_invalid_participants():
    with pytest.raises(ValidationError):
        make(participants=0)
