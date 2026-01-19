import pdfplumber
import re
import spacy
from sentence_transformers import SentenceTransformer, util

nlp=spacy.load("en_core_web_sm")

model=SentenceTransformer('all-MiniLM-L6-v2')

def extract_text(pdf_path):
    text=""

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text+=page.extract_text() + " "
    return text

def clean_text(text):
    text = re.sub(r'[^a-zA-Z]', ' ',text)
    text=text.lower()
    doc=nlp(text)
    tokens=[token.lemma_ for token in doc if not token.is_stop]
    return " ".join(tokens)


def get_embeddings(texts):
    return model.encode(texts,convert_to_tensor=True)


def rank_resumes(resume_files,jd_text):
    jd_clean = clean_text(jd_text)
    jd_emb=get_embeddings(jd_clean)

    results=[]

    for file in resume_files:
        res_text=extract_text(file)
        res_clean=clean_text(res_text)
        res_emb=get_embeddings(res_clean)
        score=util.cos_sim(res_emb,jd_emb).item()
        results.append((file,score))

    return sorted(results,key=lambda x:x[1],reverse=True)