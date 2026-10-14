from datetime import date
from pydantic import BaseModel, Field

class EventInfo(BaseModel):
    event_name: str = Field(min_length=3)
    organizer: str = Field(min_length=2)
    event_date: date
    venue: str = Field(min_length=2)
    participants: int = Field(gt=0)
    description: str = Field(min_length=10)
    highlights: list[str] = Field(default_factory=list)
    tone: str = "formal"

    @property
    def day(self) -> str:
        return self.event_date.strftime("%A")
