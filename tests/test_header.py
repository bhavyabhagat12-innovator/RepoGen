import base64
import io

from PIL import Image

from repogen.header import Header, prepare_logo


def test_empty_header():
    assert Header().is_empty


def test_header_with_text_is_not_empty():
    assert not Header(lines=["My College"]).is_empty


def test_prepare_logo_returns_valid_png():
    buf = io.BytesIO()
    Image.new("RGB", (1200, 800), "red").save(buf, format="JPEG")
    b64 = prepare_logo(buf.getvalue())
    img = Image.open(io.BytesIO(base64.b64decode(b64)))
    assert img.format == "PNG"
    assert max(img.size) <= 600