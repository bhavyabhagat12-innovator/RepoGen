import base64
import io

from PIL import Image, ImageOps
from pydantic import BaseModel, Field

MAX_PHOTO_PX = 1200


class Photo(BaseModel):
    image_b64: str
    caption: str = Field(default="", max_length=150)

    @property
    def image_bytes(self) -> bytes:
        return base64.b64decode(self.image_b64)


def prepare_photo(raw: bytes) -> str:
    """Validate an uploaded image, fix rotation, shrink it, convert to JPEG, return base64 text."""
    img = Image.open(io.BytesIO(raw))
    img.load()
    img = ImageOps.exif_transpose(img)
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGBA")
        background = Image.new("RGB", img.size, "white")
        background.paste(img, mask=img.split()[-1])
        img = background
    else:
        img = img.convert("RGB")
    img.thumbnail((MAX_PHOTO_PX, MAX_PHOTO_PX))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode()
