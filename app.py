import streamlit as st
from pydantic import ValidationError

from repogen.exporters import to_docx, to_pdf
from repogen.generator import generate_report
from repogen.schemas import EventInfo

st.set_page_config(page_title="RepoGen", page_icon="📝", layout="centered")
st.title("📝 RepoGen")
st.caption("Fill in the event details and get a ready-to-edit report.")

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

    c1, c2 = st.columns(2)
    c1.download_button(
        "⬇️ Download DOCX",
        to_docx(report),
        "report.docx",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    c2.download_button("⬇️ Download PDF", to_pdf(report), "report.pdf", "application/pdf")
