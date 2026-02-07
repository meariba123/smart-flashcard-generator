import re
import random
import os
import spacy
from docx import Document
from PyPDF2 import PdfReader
from pptx import Presentation
from PIL import Image
import pytesseract
from rapidfuzz import fuzz

# Load spaCy
try:
    nlp = spacy.load("en_core_web_sm")
except:
    os.system("python -m spacy download en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# --- REFINED JUNK LIST ---
EXACT_JUNK = {'this', 'that', 'it', 'they', 'there', 'what', 'which', 'who', 'example', 'examples'}
PREFIX_JUNK = r'^(e\.g\.|i\.e\.|etc|example:|note:)\s+'

def clean_term(term):
    """Cleans prefixes like 'e.g.' from the start of questions."""
    term = re.sub(PREFIX_JUNK, '', term, flags=re.IGNORECASE)
    return term.strip().capitalize()

def clean_text(text):
    """Removes slide junk like URLs and common filler."""
    text = re.sub(r'https?://\S+', '', text) 
    text = re.sub(r'\(.*?\)', '', text)      
    text = text.replace(' - ', ' ').replace(' : ', ' ')
    return text.strip()

# --- FILE EXTRACTION ---
def extract_text_from_file(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    text = ""
    try:
        if ext == ".txt":
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        elif ext == ".docx":
            doc = Document(filepath)
            text = "\n".join([para.text for para in doc.paragraphs])
        elif ext == ".pdf":
            reader = PdfReader(filepath)
            text = "\n".join([page.extract_text() or "" for page in reader.pages])
        elif ext in [".png", ".jpg", ".jpeg"]:
            text = pytesseract.image_to_string(Image.open(filepath))
        elif ext == ".pptx":
            prs = Presentation(filepath)
            full_text = []
            for slide in prs.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text.strip():
                        full_text.append(shape.text)
                    elif shape.has_table:
                        for row in shape.table.rows:
                            for cell in row.cells:
                                if cell.text.strip():
                                    full_text.append(cell.text)
            text = "\n".join(full_text)
    except Exception as e:
        print(f"Error extracting text: {e}")
    return text

# --- FLASHCARD GENERATION ---
def generate_flashcards_from_file(filepath):
    text = extract_text_from_file(filepath)
    if not text.strip(): return []
    
    flashcards = []
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line or len(line) < 5: continue

        # 1. Colon Logic (Term: Definition)
        if ":" in line:
            parts = line.split(":", 1)
            term = clean_term(parts[0])
            definition = clean_text(parts[1])
            
            if term.lower() not in EXACT_JUNK and 1 <= len(term.split()) <= 7:
                if len(definition) > 5:
                    flashcards.append({"question": f"What is {term}?", "answer": definition, "score": 0.80})
                    continue

        # 2. Regex Logic (X is a Y)
        match = re.search(r'^(.+?)\s+(is|are|means|refers to)\s+(.+)', line, re.I)
        if match:
            term = clean_term(match.group(1))
            definition = clean_text(match.group(3))
            
            if term.lower() not in EXACT_JUNK and len(term.split()) <= 7:
                term_doc = nlp(term)
                if any(t.pos_ in ['NOUN', 'PROPN'] for t in term_doc):
                    flashcards.append({"question": f"What is {term}?", "answer": definition, "score": 0.75})

    # 3. Formula Logic
    formula_matches = re.findall(r'([A-Za-z0-9_]+\s*=\s*[^.\n]+)', text)
    for f in formula_matches:
        if any(op in f for op in ["+", "-", "*", "/", "^"]):
            flashcards.append({"question": "Explain this formula/expression:", "answer": f.strip(), "score": 0.90})

    unique_results = {c['question'].lower(): c for c in flashcards}.values()
    final_list = list(unique_results)
    random.shuffle(final_list)
    return final_list

def is_answer_correct(user_answer, correct_answer, threshold=75):
    user_answer = user_answer.lower().strip()
    correct_answer = correct_answer.lower().strip()
    similarity = fuzz.ratio(user_answer, correct_answer)
    if similarity >= threshold: return True
    user_keywords = set(user_answer.split())
    correct_keywords = set(correct_answer.split())
    if len(correct_keywords) > 0:
        overlap = len(user_keywords & correct_keywords) / len(correct_keywords)
        if overlap > 0.6: return True
    return False