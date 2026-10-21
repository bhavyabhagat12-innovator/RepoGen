import base64
import io
import re

from PIL import Image
from pydantic import BaseModel, Field, field_validator

MAX_LOGO_PX = 600
HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")
B64 = re.compile(r"^[A-Za-z0-9+/]+={0,2}$")
MAX_B64_CHARS = 2_000_000


def _check_color(v: str) -> str:
    if not HEX.match(v):
        raise ValueError("color must look like #RRGGBB")
    return v


class HeaderLine(BaseModel):
    text: str = Field(max_length=200)
    bold: bool = True
    color: str = "#000000"
    size: int = Field(default=12, ge=8, le=28)

    _color = field_validator("color")(classmethod(lambda cls, v: _check_color(v)))


class Header(BaseModel):
    left_logo_b64: str | None = None
    right_logo_b64: str | None = None
    lines: list[HeaderLine] = Field(default_factory=list, max_length=8)
    strip: list[str] = Field(default_factory=list, max_length=4)
    strip_color: str = "#0070C0"

    @field_validator("left_logo_b64", "right_logo_b64")
    @classmethod
    def _check_image(cls, v):
        if v is None:
            return v
        if len(v) > MAX_B64_CHARS or not B64.match(v):
            raise ValueError("invalid image data")
        return v

    @field_validator("strip_color")
    @classmethod
    def _check_strip_color(cls, v):
        return _check_color(v)

    @property
    def left_logo_bytes(self) -> bytes | None:
        return base64.b64decode(self.left_logo_b64) if self.left_logo_b64 else None

    @property
    def right_logo_bytes(self) -> bytes | None:
        return base64.b64decode(self.right_logo_b64) if self.right_logo_b64 else None

    @property
    def is_empty(self) -> bool:
        return not (self.lines or self.strip or self.left_logo_b64 or self.right_logo_b64)


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