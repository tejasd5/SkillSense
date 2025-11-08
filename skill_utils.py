# skill_utils.py
import re
import json
from pathlib import Path
from sentence_transformers import SentenceTransformer, util

MODEL = SentenceTransformer('all-MiniLM-L6-v2')  # small & fast

BASE_DIR = Path(__file__).parent

with open(BASE_DIR / "skills_ontology.json", "r", encoding="utf8") as f:
    CANONICAL_SKILLS = json.load(f)

# Precompute embeddings
CANONICAL_EMBS = MODEL.encode(CANONICAL_SKILLS, convert_to_tensor=True)

def extract_text_from_pdf_bytes(bytes_io):
    import pdfplumber
    with pdfplumber.open(bytes_io) as pdf:
        text = []
        for page in pdf.pages:
            text.append(page.extract_text() or "")
    return "\n".join(text)

def simple_text_cleanup(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9\.\,\-\n ]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text

def keyword_match(text):
    """Exact/substring matches against ontology"""
    found = set()
    t = text.lower()
    for skill in CANONICAL_SKILLS:
        if skill in t:
            found.add(skill)
    return list(found)

def embedding_match(text, top_k=6, threshold=0.55):
    """Use sentence-transformer to find similar canonical skills for phrases in text."""
    sentences = re.split(r'[.\n]', text)
    sentences = [s.strip() for s in sentences if len(s.strip())>3]
    if not sentences:
        return []
    sent_embs = MODEL.encode(sentences, convert_to_tensor=True)
    hits = {}
    cos_scores = util.cos_sim(sent_embs, CANONICAL_EMBS)
    import torch
    for i, sent in enumerate(sentences):
        scores = cos_scores[i]
        top_results = torch.topk(scores, k=min(top_k, scores.shape[0]))
        for score, idx in zip(top_results.values, top_results.indices):
            score = float(score)
            skill = CANONICAL_SKILLS[int(idx)]
            if score >= threshold:
                if skill not in hits or hits[skill] < score:
                    hits[skill] = score
    sorted_hits = sorted(hits.items(), key=lambda x: -x[1])
    return [s for s, sc in sorted_hits]

def extract_skills_from_text(text):
    t = simple_text_cleanup(text)
    exact = set(keyword_match(t))
    embed = set(embedding_match(t))
    combined = list(exact.union(embed))
    return combined

def compare_with_role(user_skills, role_name):
    with open(BASE_DIR / "roles.json","r",encoding="utf8") as f:
        roles = json.load(f)
    role_skills = roles.get(role_name, [])
    have = [s for s in role_skills if s in user_skills]
    missing = [s for s in role_skills if s not in user_skills]
    extra = [s for s in user_skills if s not in role_skills]
    return {"role": role_name, "have": have, "missing": missing, "extra": extra}
