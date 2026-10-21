import base64
import io

from PIL import Image
from pydantic import BaseModel, Field

MAX_LOGO_PX = 600


class Header(BaseModel):
    lines: list[str] = Field(default_factory=list)
    logo_b64: str | None = None

    @property
    def logo_bytes(self) -> bytes | None:
        return base64.b64decode(self.logo_b64) if self.logo_b64 else None

    @property
    def is_empty(self) -> bool:
        return not self.lines and not self.logo_b64


def prepare_logo(raw: bytes) -> str:
    """Validate an uploaded image, shrink it, convert to PNG, return base64 text."""
    img = Image.open(io.BytesIO(raw))
    img.load()
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGBA")
    img.thumbnail((MAX_LOGO_PX, MAX_LOGO_PX))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()