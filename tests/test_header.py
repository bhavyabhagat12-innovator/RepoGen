import base64
import io

import pytest
from PIL import Image
from pydantic import ValidationError

from repogen.exporters import to_docx, to_pdf
from repogen.header import Header, HeaderLine, prepare_logo


def make_png_b64() -> str:
    buf = io.BytesIO()
    Image.new("RGB", (1200, 800), "red").save(buf, format="JPEG")
    return prepare_logo(buf.getvalue())


def test_empty_header():
    assert Header().is_empty


def test_header_with_text_is_not_empty():
    assert not Header(lines=[HeaderLine(text="My College")]).is_empty


def test_prepare_logo_returns_valid_png():
    img = Image.open(io.BytesIO(base64.b64decode(make_png_b64())))
    assert img.format == "PNG"
    assert max(img.size) <= 600


def test_bad_color_rejected():
    with pytest.raises(ValidationError):
        HeaderLine(text="x", color="red")


def test_bad_image_data_rejected():
    with pytest.raises(ValidationError):
        Header(left_logo_b64='"><script>')


def test_exports_with_full_header():
    logo = make_png_b64()
    header = Header(
        left_logo_b64=logo,
        right_logo_b64=logo,
        lines=[HeaderLine(text="My College"), HeaderLine(text="Dept", color="#C00000")],
        strip=["Approved by AICTE", "Accredited by NAAC", "Affiliated to SPPU"],
    )
    report = {
        "title": "Report on Test",
        "meta": {"Venue": "Hall"},
        "sections": [{"heading": "Introduction", "text": "Some text."}],
    }
    assert to_docx(report, header)[:2] == b"PK"
    assert to_pdf(report, header)[:4] == b"%PDF"