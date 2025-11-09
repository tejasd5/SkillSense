# app.py (FULL - replace your current app.py with this)
import streamlit as st
from pathlib import Path
import json
import time
import matplotlib.pyplot as plt
import numpy as np
import re
import html

# import skill utilities
try:
    from skill_utils import (
        extract_text_from_pdf_bytes,
        extract_text_from_docx,
        extract_skills_from_text,
        compare_user_with_role_skills,
        fetch_github_profile_readme,
        fetch_github_languages,
        fetch_linkedin_public_text,
        load_canonical_skills_and_embeddings
    )
except Exception as e:
    st.error(
        "Could not import skill_utils. Make sure skill_utils.py exists and defines the required functions.\n\n"
        f"Import error: {e}"
    )
    st.stop()

# ---- Page config and theme guidance ----
st.set_page_config(page_title="SkillSense AI", page_icon="🧠", layout="wide")

# -------------------------
# Utility: highlight function
# -------------------------
def highlight_text(text: str, matched: list):
    """
    Return HTML-safe text with matched skill phrases highlighted.
    - sorts matched by length desc to avoid partial overlapping replacements
    - uses re.sub with (?i) for case-insensitive replacement
    - escapes original text first to avoid breaking HTML
    """
    if not text:
        return ""
    safe = html.escape(text)
    matched_sorted = sorted([m for m in (matched or []) if m], key=lambda s: -len(s))
    highlighted = safe
    for sk in matched_sorted:
        try:
            # whole-word-ish, case-insensitive
            pattern = r'(?i)\b' + re.escape(sk) + r'\b'
            highlighted = re.sub(pattern, f"<mark style='background:#a7f3d0'>{sk}</mark>", highlighted)
        except re.error:
            try:
                highlighted = re.sub(re.escape(sk), f"<mark style='background:#a7f3d0'>{sk}</mark>", highlighted, flags=re.IGNORECASE)
            except Exception:
                pass
    return highlighted

# ---- Sidebar: settings, sample inputs, mode ----
st.sidebar.title("SkillSense Controls")
st.sidebar.markdown("**Demo helpers**")
st.sidebar.markdown("- Choose `Fast mode` for instant keyword-only matching.")
st.sidebar.markdown("- Use `Precomputed embeddings` if you ran precompute script.")

fast_mode = st.sidebar.checkbox("Fast Mode (keyword only, fastest)", value=False)
use_precomputed = st.sidebar.checkbox("Use precomputed canonical_embs.npy (if available)", value=False)
precomputed_path = "canonical_embs.npy" if use_precomputed else None

st.sidebar.divider()
st.sidebar.header("Sample inputs")
sample_choice = st.sidebar.selectbox("Load example resume", ["None", "Junior Data Scientist", "Backend Developer", "Product Manager"])
if st.sidebar.button("Load sample into input"):
    if sample_choice == "Junior Data Scientist":
        sample_text = "John Doe. Built ML models for churn using Python, pandas, scikit-learn. Deployed using Docker and AWS. Proficient in SQL and data analysis."
    elif sample_choice == "Backend Developer":
        sample_text = "Jane Doe. Developed RESTful APIs using Flask and FastAPI. Dockerized services, CI/CD with Jenkins. Strong knowledge of Linux, git, and PostgreSQL."
    elif sample_choice == "Product Manager":
        sample_text = "Alex PM. Managed product roadmaps, stakeholder communication, KPI tracking, and data-driven decisions. Familiar with SQL and A/B testing."
    else:
        sample_text = ""
    st.session_state["sample_text"] = sample_text

st.sidebar.divider()
st.sidebar.header("GitHub / LinkedIn (optional)")
gh_username = st.sidebar.text_input("GitHub username (optional)")
gh_token = st.sidebar.text_input("GitHub token (optional, increase rate limit)", type="password")
li_url = st.sidebar.text_input("LinkedIn public profile URL (optional)")

st.sidebar.divider()
st.sidebar.markdown("Version: 1.2 — Polished UI")

# ---- Load grouped roles.json (profile -> role -> skills) ----
BASE = Path(__file__).parent
roles_path = BASE / "roles.json"
if not roles_path.exists():
    st.error("roles.json missing. Add roles.json (grouped roles) to project root.")
    st.stop()
grouped_roles = json.load(open(roles_path, "r", encoding="utf8"))

# ---- App header / hero ----
st.title("🧠 SkillSense AI — Identify skills, close gaps")
st.write("Upload a resume (PDF/TXT/DOCX), paste LinkedIn/GitHub text, or provide GitHub username / LinkedIn URL. Choose a profile → role and click Analyze.")

# ---- Upload area and paste area ----
colA, colB = st.columns([2, 1])
with colA:
    uploaded = st.file_uploader("Drop a file (PDF, TXT, DOCX) or use the textbox below", type=["pdf", "txt", "docx"])
    text_input = st.text_area("Or paste LinkedIn/GitHub/resume text here", height=220, value=st.session_state.get("sample_text", ""))
with colB:
    st.markdown("**Quick tips**")
    st.markdown("- If PDF is scanned (image), copy-paste text instead.")
    st.markdown("- Use GitHub username to auto-extract README + repo descriptions.")
    st.markdown("- LinkedIn scraping is best-effort; if it fails paste profile text manually.")

# ---- Profile -> Role selection UI ----
profile_names = list(grouped_roles.keys())
selected_profile = st.selectbox("Select Profile (category):", profile_names)
roles_in_profile = list(grouped_roles[selected_profile].keys())
selected_role = st.selectbox("Select Role:", roles_in_profile)
role_skill_list = grouped_roles[selected_profile][selected_role]

# ---- Helper: gather text from uploads / GH / LinkedIn ----
raw_text = ""
if uploaded:
    if uploaded.type == "application/pdf" or str(uploaded.name).lower().endswith(".pdf"):
        try:
            raw_text = extract_text_from_pdf_bytes(uploaded)
        except Exception as e:
            st.warning("PDF extraction issue, try pasting text. " + str(e))
    elif uploaded.type in ("application/vnd.openxmlformats-officedocument.wordprocessingml.document",) or str(uploaded.name).lower().endswith(".docx"):
        try:
            raw_text = extract_text_from_docx(uploaded)
        except Exception as e:
            st.warning("DOCX extraction issue, try pasting text. " + str(e))
    else:
        try:
            raw_text = uploaded.getvalue().decode("utf-8", errors="ignore")
        except Exception:
            raw_text = ""
# If GitHub username provided, append GH readme/desc
if gh_username:
    with st.spinner("Fetching GitHub profile..."):
        gh_text = fetch_github_profile_readme(gh_username, token=gh_token, max_repos=8)
        lang_info = fetch_github_languages(gh_username, token=gh_token, max_repos=12)
        if gh_text:
            raw_text = (raw_text + "\n\n" + gh_text).strip()
# LinkedIn public text
if li_url:
    with st.spinner("Fetching LinkedIn public page (may be incomplete)..."):
        li_text = fetch_linkedin_public_text(li_url)
        if li_text:
            raw_text = (raw_text + "\n\n" + li_text).strip()
# If user pasted text, prefer that (non-empty)
if text_input and text_input.strip():
    raw_text = text_input

# ---- Analysis: Run when button clicked ----
analyze = st.button("🚀 Analyze My Skills")
if analyze:
    if not raw_text or len(raw_text.strip()) < 10:
        st.warning("Please upload or paste a valid resume / profile text, or provide a GitHub username.")
    else:
        # show progress + lazy model load
        with st.spinner("Preparing model and running extraction..."):
            t0 = time.time()
            # choose use_embeddings boolean
            use_embeddings = not fast_mode
            # pass precomputed_path if available
            skills = extract_skills_from_text(
                raw_text,
                use_embeddings=use_embeddings,
                threshold=0.56,
                max_sentences=40,
                precomputed_emb_path=precomputed_path
            )
            t1 = time.time()
            elapsed = t1 - t0

        # compare with role skills
        comp = compare_user_with_role_skills(skills, role_skill_list)

        # ------------------- DISPLAY RESULTS -------------------
        st.success("Analysis complete ✅")

        # compute matching and a simple match score
        matching_count = len(comp.get("have", []))
        missing_count = len(comp.get("missing", []))
        extra_count = len(comp.get("extra", []))
        total_required = max(1, len(role_skill_list))
        match_score = matching_count / total_required

        # top metrics: role, counts, elapsed
        top_col, m1, m2, time_col = st.columns([2,1,1,1])
        with top_col:
            st.markdown("### 🎯 Target Role")
            st.info(selected_role)
        with m1:
            st.markdown("### 🧩 Skills Detected")
            st.metric(label="Count", value=len(skills))
        with m2:
            st.markdown("### ⚡ Missing")
            st.metric(label="Count", value=missing_count)
        with time_col:
            st.markdown("### ⏱️ Time (s)")
            st.metric(label="Elapsed", value=f"{elapsed:.1f}s")

        st.divider()

        # Summary metrics row (missing, extra, matching, match score)
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Missing Skills", missing_count)
        with c2:
            st.metric("Extra Skills", extra_count)
        with c3:
            st.metric("Matching Skills", matching_count)
        with c4:
            st.metric("Match Score", f"{match_score*100:.0f}%")

        st.divider()

        # Detected skills (badges)
        st.subheader("Detected Skills")
        if skills:
            badge_cols = st.columns(5)
            for i, sk in enumerate(skills):
                badge_cols[i % 5].button(sk, key=f"skill_{i}")
        else:
            st.write("No skills detected.")

        st.divider()

        # Clean comparison display (missing + resources)
        st.subheader(f"🔎 Comparison vs {selected_role}")

        # Debug expander (optional)
        with st.expander("🧰 DEBUG - comp value (click to view)"):
            st.json(comp)

        # Missing skills with expanders and learning links
        if comp.get('missing'):
            st.markdown("### ❗ Missing Skills — click each to view learning resources")
            for i, skill in enumerate(comp['missing'], start=1):
                with st.expander(f"{i}. {skill.title()}"):
                    st.markdown(f"**Why it's important:** Mastering *{skill}* is important for this role.")
                    q = skill.replace(" ", "+")
                    st.markdown(f"- 🎓 Course: [Coursera](https://www.coursera.org/search?query={q})")
                    st.markdown(f"- 📺 Videos: [YouTube](https://www.youtube.com/results?search_query={q})")
                    st.markdown(f"- 🧠 Practice: Build a small project using **{skill}** and add to your CV.")
        else:
            st.success("🎉 Excellent! You already match all required skills for this role.")

        st.divider()

        # Extra skills display
        if comp.get('extra'):
            st.subheader("💡 Extra Skills You Have")
            st.markdown(", ".join(comp['extra']))
        else:
            st.info("No extra skills found beyond role requirements.")

        st.divider()

        # Highlight parsed resume (safe)
        st.subheader("Parsed Resume (highlights)")
        try:
            highlighted_html = highlight_text(raw_text[:8000], comp.get("have", []) + comp.get("missing", []))
            st.markdown(highlighted_html, unsafe_allow_html=True)
        except Exception:
            st.text_area("Parsed text", raw_text[:8000], height=200)

        st.divider()

        # Personalized recommendations quick links
        st.subheader("Personalized Recommendations")
        if comp.get("missing"):
            for sk in comp["missing"]:
                q = sk.replace(" ", "+")
                st.markdown(f"- **{sk}** — Quick learn: [YouTube](https://www.youtube.com/results?search_query={q}) | [Coursera](https://www.coursera.org/search?query={q})")
        else:
            st.success("You match most skills for this role! Focus on project examples & soft skills.")

        st.divider()

        # Skill coverage bar chart (by simple categories)
        st.subheader("Skill coverage (by simple categories)")
        cats = {"Programming":0, "Data/ML":0, "Cloud/Infra":0, "Design/PM":0, "Soft Skills":0}
        cat_total = {k:0 for k in cats}
        for s in role_skill_list:
            sl = s.lower()
            if any(k in sl for k in ["python","java","javascript","react","kotlin","swift","solidity"]):
                cat = "Programming"
            elif any(k in sl for k in ["machine","ml","data","pandas","numpy","tableau","power bi","spark"]):
                cat = "Data/ML"
            elif any(k in sl for k in ["aws","docker","kubernetes","terraform","ci/cd","linux","gcp","azure","jenkins"]):
                cat = "Cloud/Infra"
            elif any(k in sl for k in ["product","pm","ux","ui","figma","design","a/b","growth"]):
                cat = "Design/PM"
            else:
                cat = "Soft Skills"
            cat_total[cat] += 1
            if s in skills:
                cats[cat] += 1

        categories = list(cats.keys())
        values = [cats[c]/max(1, cat_total[c]) for c in categories]

        fig, ax = plt.subplots(figsize=(6,3))
        ax.bar(categories, values)
        ax.set_ylim(0,1)
        ax.set_ylabel("Coverage (0-1)")
        st.pyplot(fig)

        st.divider()

        # download summary
        summary = (
            f"Role: {selected_role}\n"
            f"Detected skills: {', '.join(skills)}\n"
            f"Missing: {', '.join(comp.get('missing',[]))}\n"
            f"Extracted from: GitHub({gh_username}) LinkedIn({li_url}) File({uploaded.name if uploaded else 'none'})"
        )
        st.download_button("Download summary (TXT)", summary, file_name="skills_summary.txt")

# End of app.py
