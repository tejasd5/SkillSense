# app.py
import streamlit as st
from skill_utils import extract_text_from_pdf_bytes, extract_skills_from_text, compare_with_role
from pathlib import Path
import json

st.set_page_config(page_title="SkillSense (Hackathon MVP)", layout="wide")

st.title("SkillSense — Unlock hidden potential (MVP)")
st.markdown("Upload a resume (PDF/TXT) or paste LinkedIn/GitHub text. Then pick a target role to see skill gaps.")

uploaded = st.file_uploader("Upload resume (PDF or TXT)", type=["pdf","txt"])
text_input = st.text_area("Or paste LinkedIn/GitHub/resume text here", height=200)

if uploaded:
    if uploaded.type == "application/pdf":
        bytes_io = uploaded
        text = extract_text_from_pdf_bytes(bytes_io)
    else:
        text = uploaded.getvalue().decode("utf-8")
else:
    text = text_input

BASE = Path(__file__).parent
roles = json.load(open(BASE / "roles.json","r",encoding="utf8"))
role_names = list(roles.keys())
selected_role = st.selectbox("Select target role to analyze against", role_names)

if st.button("Analyze"):
    if not text or len(text.strip()) < 10:
        st.error("Please paste resume text or upload a resume file.")
    else:
        with st.spinner("Extracting skills..."):
            skills = extract_skills_from_text(text)
        st.subheader("Detected skills")
        st.write(skills or "No skills detected — try pasting more text (profile, project descriptions)")

        comp = compare_with_role(skills, selected_role)
        st.subheader(f"Comparison vs {selected_role}")
        st.markdown(f"**Have ({len(comp['have'])})**: {comp['have']}")
        st.markdown(f"**Missing ({len(comp['missing'])})**: {comp['missing']}")
        st.markdown(f"**Other skills**: {comp['extra']}")

        st.subheader("Personalized learning recipe (MVP)")
        recs = []
        for miss in comp['missing']:
            if miss in ["python","sql","pandas"]:
                recs.append((miss, "Complete a hands-on project + DataCamp / freeCodeCamp tutorials"))
            elif miss in ["machine learning","scikit-learn","deep learning","pytorch","tensorflow"]:
                recs.append((miss, "Follow a focused ML project (Kaggle tutorial) and Coursera/fast.ai modules"))
            elif miss in ["rest api","docker","aws","kubernetes"]:
                recs.append((miss, "Build and deploy a microservice, practice Docker + cloud tutorials"))
            else:
                recs.append((miss, "Search course on Coursera/YouTube and build a sample project"))
        if not recs:
            st.success("You are well matched for this role! Consider upskilling communication/project experience.")
        else:
            for r in recs:
                st.markdown(f"- **{r[0]}** — {r[1]}")

        st.subheader("One-line summary")
        summary = f"Role: {selected_role}\nDetected skills: {', '.join(skills)}\nMissing: {', '.join(comp['missing'])}"
        st.code(summary)
        st.download_button("Download summary as TXT", summary, file_name="skills_summary.txt")
