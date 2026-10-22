import html

import streamlit as st
from pydantic import ValidationError

from repogen.exporters import to_docx, to_pdf
from repogen.generator import generate_report
from repogen.header import Header, HeaderLine, prepare_logo
from repogen.photos import Photo, prepare_photo
from repogen.schemas import EventInfo

st.set_page_config(page_title="RepoGen", page_icon="📝", layout="centered")
st.title("📝 RepoGen")
st.caption("Fill in the event details and get a ready-to-edit report.")

LINE_COLORS = ["#000000", "#C00000", "#000000", "#000000", "#000000", "#000000"]
PRESETS = {
    "100 - 200 words": (100, 200),
    "200 - 300 words": (200, 300),
    "300 - 500 words": (300, 500),
    "500 - 800 words": (500, 800),
    "800 - 1200 words": (800, 1200),
}


def show_header_preview(h: Header) -> None:
    with st.container(border=True):
        st.caption("Header preview (repeats on every page)")
        left, mid, right = st.columns([1, 4, 1])
        if h.left_logo_bytes:
            left.image(h.left_logo_bytes)
        if h.right_logo_bytes:
            right.image(h.right_logo_bytes)
        for ln in h.lines:
            weight = "700" if ln.bold else "400"
            mid.markdown(
                f"<div style='text-align:center;font-weight:{weight};color:{ln.color};"
                f"font-size:{ln.size}px;line-height:1.3'>{html.escape(ln.text)}</div>",
                unsafe_allow_html=True,
            )
        if h.strip:
            for col, item in zip(st.columns(len(h.strip)), h.strip):
                col.markdown(
                    f"<div style='text-align:center;font-weight:700;color:{h.strip_color};"
                    f"border-top:1px solid #888;border-bottom:1px solid #888'>{html.escape(item)}</div>",
                    unsafe_allow_html=True,
                )


def logo_input(label: str, key: str):
    f = st.file_uploader(label, type=["png", "jpg", "jpeg"], key=key)
    if f is None:
        return None
    try:
        return prepare_logo(f.getvalue())
    except Exception:
        st.error("Could not read that image. Please upload a valid PNG or JPG.")
        return None


# ---------------- Header section ----------------
st.subheader("Report header")

if "saved_header" not in st.session_state:
    st.session_state["saved_header"] = None

choice = st.radio(
    "Header option",
    ["No header", "Use saved header", "Create new header"],
    horizontal=True,
    label_visibility="collapsed",
    key="header_choice",
)

header = None

if choice == "Create new header":
    c1, c2 = st.columns(2)
    with c1:
        left_b64 = logo_input("Left logo (optional)", "left_logo")
    with c2:
        right_b64 = logo_input("Right logo (optional)", "right_logo")

    n_lines = int(st.number_input("Number of text lines", min_value=0, max_value=6, value=3))
    lines = []
    for i in range(n_lines):
        a, b, c, d = st.columns([5, 1.4, 1.2, 1])
        text = a.text_input(f"Line {i + 1}", key=f"hl_text_{i}")
        size = b.number_input("Size", min_value=8, max_value=28, value=12, key=f"hl_size_{i}")
        color = c.color_picker("Color", LINE_COLORS[i], key=f"hl_color_{i}")
        bold = d.checkbox("Bold", value=True, key=f"hl_bold_{i}")
        if text.strip():
            lines.append(HeaderLine(text=text.strip(), bold=bold, color=color, size=int(size)))

    st.markdown("**Strip under the header (optional, up to 3 items)**")
    strip_items = [
        col.text_input(f"Item {i + 1}", key=f"strip_{i}").strip()
        for i, col in enumerate(st.columns(3))
    ]
    strip_items = [s for s in strip_items if s]
    strip_color = st.color_picker("Strip text color", "#0070C0", key="strip_color")
    remember = st.checkbox("Remember this header for next time", value=True)

    candidate = Header(
        left_logo_b64=left_b64,
        right_logo_b64=right_b64,
        lines=lines,
        strip=strip_items,
        strip_color=strip_color,
    )
    if not candidate.is_empty:
        header = candidate
        if remember:
            st.session_state["saved_header"] = candidate

elif choice == "Use saved header":
    if st.session_state["saved_header"] is not None:
        header = st.session_state["saved_header"]
    else:
        st.info("No saved header yet. Choose 'Create new header' and tick 'Remember this header'.")

if header is not None:
    show_header_preview(header)

with st.expander("Save or load a header file"):
    saved = st.session_state["saved_header"]
    if saved is not None:
        st.download_button(
            "Download saved header", saved.model_dump_json(), "repogen_header.json", "application/json"
        )
    else:
        st.caption("Create a header with 'Remember' ticked to enable downloading it.")

    loaded = st.file_uploader("Load a header file", type=["json"], key="header_file")
    if loaded is not None:
        marker = f"{loaded.name}-{loaded.size}"
        if st.session_state.get("last_import") != marker:
            try:
                st.session_state["saved_header"] = Header.model_validate_json(loaded.getvalue())
                st.session_state["last_import"] = marker
                st.rerun()
            except Exception:
                st.error("That file is not a valid RepoGen header file.")

st.divider()

# ---------------- Report length ----------------
st.subheader("Report length")
length_choice = st.selectbox("Total words in the report body", list(PRESETS) + ["Custom"], index=1)
if length_choice == "Custom":
    w1, w2 = st.columns(2)
    min_words = int(w1.number_input("Minimum words", min_value=50, max_value=2000, value=200, step=50))
    max_words = int(w2.number_input("Maximum words", min_value=50, max_value=2000, value=400, step=50))
else:
    min_words, max_words = PRESETS[length_choice]
st.caption("The AI aims for this range; the actual count is shown after generation. Longer reports read better with more highlights.")

st.divider()

# ---------------- Photos ----------------
st.subheader("Photos (optional)")
MAX_PHOTOS = 8
MAX_FILE_MB = 8

photo_files = st.file_uploader(
    f"Upload event photos (PNG or JPG, up to {MAX_PHOTOS})",
    type=["png", "jpg", "jpeg"],
    accept_multiple_files=True,
    key="photos",
)
if len(photo_files) > MAX_PHOTOS:
    st.warning(f"Only the first {MAX_PHOTOS} photos will be used.")
    photo_files = photo_files[:MAX_PHOTOS]

photos = []
for i, f in enumerate(photo_files):
    if f.size > MAX_FILE_MB * 1024 * 1024:
        st.error(f"{f.name} is larger than {MAX_FILE_MB} MB and was skipped.")
        continue
    try:
        b64 = prepare_photo(f.getvalue())
    except Exception:
        st.error(f"Could not read {f.name}. Please upload a valid PNG or JPG.")
        continue
    img_col, cap_col = st.columns([1, 3])
    img_col.image(f.getvalue(), width=110)
    caption = cap_col.text_input("Caption (optional)", key=f"cap_{i}_{f.name}")
    photos.append(Photo(image_b64=b64, caption=caption.strip()))

st.divider()

# ---------------- Event form ----------------
with st.form("event_form"):
    event_name = st.text_input("Event name")
    organizer = st.text_input("Organized by (department / club)")
    col1, col2 = st.columns(2)
    event_date = col1.date_input("Date")
    participants = col2.number_input("Number of participants", min_value=0, step=1)
    venue = st.text_input("Venue")
    description = st.text_area("Event description")
    highlights_raw = st.text_area("Highlights (one per line)")
    tone = st.selectbox("Tone", ["formal", "semi-formal", "enthusiastic"])
    submitted = st.form_submit_button("Generate report")

if submitted:
    if min_words >= max_words:
        st.error("Minimum words must be smaller than maximum words.")
    else:
        try:
            event = EventInfo(
                event_name=event_name,
                organizer=organizer,
                event_date=event_date,
                venue=venue,
                participants=int(participants),
                description=description,
                highlights=[h.strip() for h in highlights_raw.splitlines() if h.strip()],
                tone=tone,
            )
            with st.spinner("Writing your report..."):
                report = generate_report(event, min_words, max_words)
            st.session_state["report"] = report
            for i, s in enumerate(report["sections"]):
                st.session_state[f"sec_{i}"] = s["text"]
        except ValidationError as err:
            for e in err.errors():
                st.error(f"{e['loc'][0]}: {e['msg']}")
        except Exception as err:
            st.error(f"Could not generate the report: {err}")

if "report" in st.session_state:
    report = st.session_state["report"]
    st.divider()
    st.subheader(report["title"])
    for k, v in report["meta"].items():
        st.markdown(f"**{k}:** {v}")

    st.markdown("### Edit sections")
    for i, s in enumerate(report["sections"]):
        s["text"] = st.text_area(s["heading"], key=f"sec_{i}", height=160)

    total = sum(len(s["text"].split()) for s in report["sections"])
    st.caption(f"Total words in the report body: {total}")
    st.caption("Exporting without a header." if header is None else "Exporting with the header shown above.")
    if photos:
        st.caption(f"{len(photos)} photo(s) will be added at the end of the report.")

    c1, c2 = st.columns(2)
    c1.download_button(
        "⬇️ Download DOCX",
        to_docx(report, header, photos),
        "report.docx",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    c2.download_button("⬇️ Download PDF", to_pdf(report, header, photos), "report.pdf", "application/pdf")
