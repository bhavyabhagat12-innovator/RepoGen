from .llm import generate_text
from .schemas import EventInfo

# name: (instruction, share of the total word count)
SECTIONS = {
    "Introduction": ("Write an introduction presenting the event and its purpose.", 0.15),
    "Objectives": ("Describe the likely objectives of the event, based on the description.", 0.15),
    "Event Summary": ("Write a detailed summary of how the event took place, using the highlights.", 0.35),
    "Outcomes": ("Describe the outcomes and benefits for participants.", 0.20),
    "Conclusion": ("Write a short conclusion, including thanks to the organizers and participants.", 0.15),
}


def split_budget(min_words: int, max_words: int) -> dict[str, tuple[int, int]]:
    """Split a total word range across the sections."""
    budget = {}
    for name, (_, share) in SECTIONS.items():
        lo = max(10, round(min_words * share))
        hi = max(lo + 10, round(max_words * share))
        budget[name] = (lo, hi)
    return budget


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


def _write_section(system: str, facts: str, instruction: str, lo: int, hi: int) -> str:
    prompt = f"Facts:\n{facts}\n\nTask: {instruction}\nLength: between {lo} and {hi} words."
    max_tokens = hi * 2 + 800  # room for the model's reasoning plus the text
    text = generate_text(system, prompt, max_tokens)
    n = len(text.split())
    if n < lo * 0.8 or n > hi * 1.2:  # far outside the range: retry once
        retry = (
            f"{prompt}\nYour previous draft had {n} words, which is outside the range. "
            f"Rewrite it using between {lo} and {hi} words."
        )
        text = generate_text(system, retry, max_tokens)
    return text


def generate_report(e: EventInfo, min_words: int = 200, max_words: int = 300) -> dict:
    facts = build_facts(e)
    system = (
        f"You write {e.tone} college event reports. Use ONLY the facts provided. "
        "Do not invent names, numbers, quotes, or guests. "
        "Write plain paragraphs with no headings, bullet points, or markdown."
    )
    budget = split_budget(min_words, max_words)
    sections = []
    for heading, (instruction, _) in SECTIONS.items():
        lo, hi = budget[heading]
        sections.append({"heading": heading, "text": _write_section(system, facts, instruction, lo, hi)})

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