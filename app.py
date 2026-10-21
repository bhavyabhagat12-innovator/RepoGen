import html

import streamlit as st
from pydantic import ValidationError

from repogen.exporters import to_docx, to_pdf
from repogen.generator import generate_report
from repogen.header import Header, prepare_logo
from repogen.schemas import EventInfo

st.set_page_config(page_title="RepoGen", page_icon="📝", layout="centered")
st.title("📝 RepoGen")
st.caption("Fill in the event details and get a ready-to-edit report.")


def show_header_preview(h: Header) -> None:
    with st.container(border=True):
        st.caption("Header preview")
        if h.logo_bytes:
            st.image(h.logo_bytes, width=100)
        for i, line in enumerate(h.lines):
            text = html.escape(line)
            st.markdown(f"**{text}**" if i == 0 else text)


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
    lines_text = st.text_area(
        "Header text (one line per row; the first line is shown bold as the title)",
        placeholder="ABC College of Engineering\nDepartment of AI and Data Science\nPune, Maharashtra",
        height=120,
    )
    logo_file = st.file_uploader("Logo or picture (optional)", type=["png", "jpg", "jpeg"])
    remember = st.checkbox("Remember this header for next time", value=True)

    logo_b64 = None
    if logo_file is not None:
        try:
            logo_b64 = prepare_logo(logo_file.getvalue())
        except Exception:
            st.error("Could not read that image. Please upload a valid PNG or JPG.")

    candidate = Header(
        lines=[ln.strip() for ln in lines_text.splitlines() if ln.strip()],
        logo_b64=logo_b64,
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
            "Download saved header",
            saved.model_dump_json(),
            "repogen_header.json",
            "application/json",
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
            report = generate_report(event)
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

    if header is None:
        st.caption("Exporting without a header.")
    else:
        st.caption("Exporting with the header shown above.")

    c1, c2 = st.columns(2)
    c1.download_button(
        "⬇️ Download DOCX",
        to_docx(report, header),
        "report.docx",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    c2.download_button("⬇️ Download PDF", to_pdf(report, header), "report.pdf", "application/pdf")