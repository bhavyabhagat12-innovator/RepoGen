from datetime import date
from repogen.generator import generate_report
from repogen.schemas import EventInfo

event = EventInfo(
    event_name="Tech Fest 2026",
    organizer="Department of AI and Data Science",
    event_date=date(2026, 10, 13),
    venue="Main Auditorium",
    participants=120,
    description="A one-day technical fest with coding contests and workshops.",
    highlights=["Hackathon winners awarded", "Workshop on machine learning", "Guest lecture by an alumnus"],
)

report = generate_report(event)
print(report["title"])
print(report["meta"])
for s in report["sections"]:
    print("\n##", s["heading"])
    print(s["text"])