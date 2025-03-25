import pdfplumber
import pytesseract
import fitz  
from PIL import Image
import io
import spacy
import re
from fuzzywuzzy import process
from dateutil import parser as date_parser

# Improved text extraction remains unchanged
def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print("Error using pdfplumber:", e)

    # If no text is found, try OCR with PyMuPDF and pytesseract
    if not text.strip():
        try:
            doc = fitz.open(pdf_path)
            for page in doc:
                pix = page.get_pixmap()
                img = Image.open(io.BytesIO(pix.tobytes()))
                text += pytesseract.image_to_string(img) + "\n"
        except Exception as e:
            print("Error using OCR:", e)
    return text.strip()

# Load spaCy NLP model
nlp = spacy.load("en_core_web_sm")

# Improved name extraction:
def extract_name(text):
    # First, try to use a heuristic based on the first few lines
    lines = text.splitlines()
    for line in lines[:5]:
        # Ignore lines that contain an email, phone number, or are too long
        if "@" in line or re.search(r'\d', line):
            continue
        # Assume a candidate name is usually one or two words and in title case
        words = line.strip().split()
        if 1 <= len(words) <= 3 and all(word[0].isupper() for word in words if word):
            # Exclude common false positives
            if any(bad in line.lower() for bad in ["gmail", "accra"]):
                continue
            return line.strip()
    # Fallback to spaCy NER
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ == "PERSON" and len(ent.text.split()) <= 4:
            if any(bad in ent.text.lower() for bad in ["gmail", "accra"]):
                continue
            return ent.text
    return "Unknown"

def extract_contact_info(text):
    email = re.findall(r"[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+", text)
    phone = re.findall(r"\+?\d[\d \-]{8,}\d", text)
    return {"email": email[0] if email else "Not found", "phone": phone[0] if phone else "Not found"}

def extract_skills(text, skills_list):
    found_skills = []
    for skill in skills_list:
        if skill.lower() in text.lower():
            found_skills.append(skill)
        elif process.extractOne(skill, text.split(), score_cutoff=80):
            found_skills.append(skill)
    return list(set(found_skills))

# Improved experience extraction using date range patterns
def extract_experience(text):
    # Pattern to match date ranges like "January 2022 – March 2024" or "Jan 2022 - Present"
    pattern = r'([A-Za-z]+\s+\d{4})\s*[-–]\s*([A-Za-z]+\s+\d{4}|Present|Ongoing)'
    matches = re.findall(pattern, text)
    total_years = 0.0
    for start_str, end_str in matches:
        try:
            start_date = date_parser.parse(start_str)
            if end_str.lower() in ["present", "ongoing"]:
                end_date = date_parser.parse("today")
            else:
                end_date = date_parser.parse(end_str)
            diff_years = (end_date - start_date).days / 365.25
            total_years += diff_years
        except Exception as e:
            continue
    # Fallback: if no date range found, try extracting individual four-digit years
    if total_years == 0.0:
        years = re.findall(r"\b(19|20)\d{2}\b", text)
        if len(years) >= 2:
            total_years = int(years[-1]) - int(years[0])
    return round(total_years, 1)

def match_candidate(candidate, job_req):
    # Calculate skill match ratio
    required_skills = set(job_req["skills"])
    candidate_skills = set(candidate["skills"])
    if required_skills:
        skill_match = len(candidate_skills.intersection(required_skills)) / len(required_skills)
    else:
        skill_match = 0
    # Experience match: binary check (1 if candidate meets minimum, else 0)
    exp_match = 1 if candidate["experience"] >= job_req["min_experience"] else 0
    # Weighted score: 70% skill match, 30% experience match
    score = (skill_match * 0.7) + (exp_match * 0.3)
    return score

def rank_candidates(candidates, job_req):
    ranked = sorted(candidates, key=lambda c: match_candidate(c, job_req), reverse=True)
    return ranked[:5]  # Returns top 5 candidates

# Example usage for testing purposes:
if __name__ == "__main__":
    # For debugging; remove or comment out in production.
    sample_text = extract_text_from_pdf("sample_resume.pdf")
    print("Extracted Name:", extract_name(sample_text))
    print("Experience:", extract_experience(sample_text))
