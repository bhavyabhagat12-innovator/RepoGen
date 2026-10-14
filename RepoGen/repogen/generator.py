from .llm import generate_text
from .schemas import EventInfo

SECTIONS = {
    "Introduction": "Write an introduction paragraph (3-4 sentences) presenting the event and its purpose.",
    "Objectives": "Write a paragraph (3-4 sentences) describing the likely objectives of the event, based on the description.",
    "Event Summary": "Write a detailed summary paragraph (5-6 sentences) of how the event took place, using the highlights.",
    "Outcomes": "Write a paragraph (3-4 sentences) about the outcomes and benefits for participants.",
    "Conclusion": "Write a short concluding paragraph (2-3 sentences), including thanks to the organizers and participants.",
}


def build_facts(e: EventInfo) -> str:
    highlights = "\n".join(f"- {h}" for h in e.highlights) or "- (none provided)"
    return (
        f"Event name: {e.event_name}\n"
        f"Organizer: {e.organizer}\n"
        f"Date: {e.event_date.strftime('%d %B %Y')} ({e.day})\n"
        f"Venue: {e.venue}\n"
        f"Number of participants: {e.participants}\n"
        f"Description: {e.description}\n"
        f"Highlights:\n{highlights}"
    )


def generate_report(e: EventInfo) -> dict:
    facts = build_facts(e)
    system = (
        f"You write {e.tone} college event reports. Use ONLY the facts provided. "
        "Do not invent names, numbers, quotes, or guests. "
        "Write plain paragraphs with no headings, bullet points, or markdown."
    )
    sections = []
    for heading, instruction in SECTIONS.items():
        text = generate_text(system, f"Facts:\n{facts}\n\nTask: {instruction}")
        sections.append({"heading": heading, "text": text})

    return {
        "title": f"Report on {e.event_name}",
        "meta": {
            "Organized by": e.organizer,
            "Date": e.event_date.strftime("%d %B %Y"),
            "Day": e.day,
            "Venue": e.venue,
            "Participants": e.participants,
        },
        "sections": sections,
    }