from io import BytesIO
from xml.sax.saxutils import escape

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Mm, Pt, RGBColor
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .header import Header

MARGIN_IN = 0.8
CONTENT_W_IN = 8.27 - 2 * MARGIN_IN  # A4 width minus margins
SIDE_W_IN = 1.25
LOGO_MAX_W_IN = 1.1
LOGO_MAX_H_IN = 1.0


def clean(text: str) -> str:
    replacements = {
        "\u2011": "-", "\u2010": "-", "\u2013": "-", "\u2014": "-",
        "\u2018": "'", "\u2019": "'",
        "\u201c": '"', "\u201d": '"',
        "\u00a0": " ", "\u202f": " ",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def _fit(w: float, h: float, max_w: float, max_h: float) -> tuple[float, float]:
    s = min(max_w / w, max_h / h)
    return w * s, h * s


# ---------------- DOCX ----------------

def _bottom_border(paragraph) -> None:
    pPr = paragraph._p.get_or_add_pPr()
    borders = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    for key, value in (("w:val", "single"), ("w:sz", "8"), ("w:space", "1"), ("w:color", "000000")):
        bottom.set(qn(key), value)
    borders.append(bottom)
    pPr.append(borders)


def _cell_top_bottom_borders(cell) -> None:
    tcPr = cell._tc.get_or_add_tcPr()
    borders = OxmlElement("w:tcBorders")
    for edge in ("top", "bottom"):
        el = OxmlElement(f"w:{edge}")
        for key, value in (("w:val", "single"), ("w:sz", "8"), ("w:space", "0"), ("w:color", "000000")):
            el.set(qn(key), value)
        borders.append(el)
    tcPr.append(borders)


def _docx_logo(cell, data: bytes | None, align) -> None:
    p = cell.paragraphs[0]
    p.alignment = align
    p.paragraph_format.space_after = Pt(0)
    if data:
        with PILImage.open(BytesIO(data)) as im:
            w, h = im.size
        tw, th = _fit(w, h, LOGO_MAX_W_IN, LOGO_MAX_H_IN)
        p.add_run().add_picture(BytesIO(data), width=Inches(tw), height=Inches(th))


def _docx_header(doc, header: Header) -> None:
    hdr = doc.sections[0].header
    hdr.is_linked_to_previous = False
    placeholder = hdr.paragraphs[0]

    top = hdr.add_table(1, 3, Inches(CONTENT_W_IN))
    top.autofit = False
    widths = [SIDE_W_IN, CONTENT_W_IN - 2 * SIDE_W_IN, SIDE_W_IN]
    left, mid, right = top.rows[0].cells
    for cell, w in zip(top.rows[0].cells, widths):
        cell.width = Inches(w)
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

    _docx_logo(left, header.left_logo_bytes, WD_ALIGN_PARAGRAPH.LEFT)
    _docx_logo(right, header.right_logo_bytes, WD_ALIGN_PARAGRAPH.RIGHT)

    for i, ln in enumerate(header.lines):
        p = mid.paragraphs[0] if i == 0 else mid.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(0)
        run = p.add_run(ln.text)
        run.bold = ln.bold
        run.font.size = Pt(ln.size)
        run.font.color.rgb = RGBColor.from_string(ln.color.lstrip("#").upper())

    if header.strip:
        n = len(header.strip)
        strip = hdr.add_table(1, n, Inches(CONTENT_W_IN))
        strip.autofit = False
        for cell, text in zip(strip.rows[0].cells, header.strip):
            cell.width = Inches(CONTENT_W_IN / n)
            _cell_top_bottom_borders(cell)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_after = Pt(0)
            run = p.add_run(text)
            run.bold = True
            run.font.size = Pt(11)
            run.font.color.rgb = RGBColor.from_string(header.strip_color.lstrip("#").upper())

    tail = hdr.add_paragraph()  # a header must end with a paragraph
    if not header.strip:
        _bottom_border(tail)
    tail.paragraph_format.space_after = Pt(0)

    placeholder._element.getparent().remove(placeholder._element)


def to_docx(report: dict, header: Header | None = None) -> bytes:
    doc = Document()
    section = doc.sections[0]
    section.page_width = Mm(210)
    section.page_height = Mm(297)
    section.left_margin = section.right_margin = Inches(MARGIN_IN)
    section.header_distance = Inches(0.3)

    if header and not header.is_empty:
        _docx_header(doc, header)

    doc.add_heading(report["title"], 0)
    for key, value in report["meta"].items():
        p = doc.add_paragraph()
        p.add_run(f"{key}: ").bold = True
        p.add_run(str(value))
    for s in report["sections"]:
        doc.add_heading(s["heading"], 1)
        for para in s["text"].split("\n\n"):
            if para.strip():
                doc.add_paragraph(para.strip())
    buf = BytesIO()
    doc.save(buf)
    return buf.getvalue()


# ---------------- PDF ----------------

def _pdf_logo(data: bytes | None, align: str):
    if not data:
        return ""
    with PILImage.open(BytesIO(data)) as im:
        w, h = im.size
    tw, th = _fit(w, h, LOGO_MAX_W_IN * 72, LOGO_MAX_H_IN * 72)
    img = Image(BytesIO(data), width=tw, height=th)
    img.hAlign = align
    return img


def _pdf_header_flowables(header: Header, content_w: float) -> list:
    center = []
    for ln in header.lines:
        style = ParagraphStyle(
            "hl",
            fontName="Helvetica-Bold" if ln.bold else "Helvetica",
            fontSize=ln.size,
            leading=ln.size * 1.25,
            alignment=TA_CENTER,
            textColor=colors.HexColor(ln.color),
        )
        center.append(Paragraph(escape(clean(ln.text)), style))
    if not center:
        center = [""]

    side = SIDE_W_IN * 72
    top = Table(
        [[_pdf_logo(header.left_logo_bytes, "LEFT"), center, _pdf_logo(header.right_logo_bytes, "RIGHT")]],
        colWidths=[side, content_w - 2 * side, side],
    )
    top.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    items = [top, Spacer(1, 4)]

    if header.strip:
        n = len(header.strip)
        style = ParagraphStyle(
            "hs", fontName="Helvetica-Bold", fontSize=10.5, leading=13,
            alignment=TA_CENTER, textColor=colors.HexColor(header.strip_color),
        )
        strip = Table(
            [[Paragraph(escape(clean(x)), style) for x in header.strip]],
            colWidths=[content_w / n] * n,
        )
        strip.setStyle(TableStyle([
            ("LINEABOVE", (0, 0), (-1, 0), 0.8, colors.black),
            ("LINEBELOW", (0, 0), (-1, 0), 0.8, colors.black),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))
        items.append(strip)
    else:
        rule = Table([[""]], colWidths=[content_w], rowHeights=[2])
        rule.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, 0), 0.8, colors.black)]))
        items.append(rule)
    return items


def to_pdf(report: dict, header: Header | None = None) -> bytes:
    buf = BytesIO()
    margin = MARGIN_IN * 72
    content_w = A4[0] - 2 * margin
    top_pad = 24

    has_header = bool(header and not header.is_empty)
    flow = _pdf_header_flowables(header, content_w) if has_header else []
    header_h = sum(f.wrap(content_w, 10_000)[1] for f in flow)
    top_margin = header_h + top_pad + 16 if has_header else 50

    pdf = SimpleDocTemplate(
        buf, pagesize=A4, leftMargin=margin, rightMargin=margin,
        topMargin=top_margin, bottomMargin=50,
    )
    styles = getSampleStyleSheet()

    story = [Paragraph(escape(clean(report["title"])), styles["Title"]), Spacer(1, 12)]
    for key, value in report["meta"].items():
        story.append(
            Paragraph(f"<b>{escape(clean(key))}:</b> {escape(clean(str(value)))}", styles["Normal"])
        )
    story.append(Spacer(1, 16))
    for s in report["sections"]:
        story.append(Paragraph(escape(clean(s["heading"])), styles["Heading2"]))
        for para in s["text"].split("\n\n"):
            if para.strip():
                story.append(Paragraph(escape(clean(para.strip())), styles["BodyText"]))
                story.append(Spacer(1, 8))

    def paint(canv, doc):
        canv.saveState()
        y = A4[1] - top_pad
        for f in flow:
            _, h = f.wrap(content_w, 10_000)
            y -= h
            f.drawOn(canv, margin, y)
        canv.restoreState()

    if has_header:
        pdf.build(story, onFirstPage=paint, onLaterPages=paint)
    else:
        pdf.build(story)
    return buf.getvalue()