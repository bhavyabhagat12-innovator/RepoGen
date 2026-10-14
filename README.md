# 📝 RepoGen

Intelligent report generator: enter event details, get a structured report written
by an open-source LLM (via Groq), then edit it and export to PDF or DOCX.

## Features
- Validated structured input (Pydantic); day of the week is calculated automatically
- Section-wise report generation with an LLM
- Editable output before download
- DOCX and PDF export
- Tone selection (formal, semi-formal, enthusiastic)

## Tech Stack
Python, Streamlit, Groq API, Pydantic, python-docx, ReportLab

## Run locally
```bash
git clone https://github.com/<your-username>/RepoGen.git
cd RepoGen
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env    # then add your own GROQ_API_KEY
streamlit run app.py
```

## Live demo
https://repogen-bbi12.streamlit.app/

## Roadmap
- [ ] More report types (meeting minutes, internship, lab)
- [ ] Saved report history
- [ ] Regenerate a single section
