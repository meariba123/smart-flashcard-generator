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

# Load spaCy for CS-specific sentence parsing
try:
    nlp = spacy.load("en_core_web_sm")
except:
    os.system("python -m spacy download en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# --- REVISED JUNK FILTER ---
# These words are blocked only if they are the ONLY word in a term
EXACT_JUNK = {
    'this', 'that', 'it', 'they', 'there', 'what', 'which', 'who', 
    'e.g.', 'i.e.', 'etc', 'example', 'examples', 'the key', 'when', 'where', 'this is'
}

def clean_text(text):
    """Removes slide junk like URLs and common filler."""
    # Remove URLs (fixes the - https issues in your screenshots)
    text = re.sub(r'https?://\S+', '', text) 
    # Remove text in parentheses (common in citations or 'e.g.' notes)
    text = re.sub(r'\(.*?\)', '', text)      
    # Clean up lingering punctuation artifacts from slides
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

# --- CS-SPECIFIC SCORING ---
def calculate_confidence(question, answer, raw_sentence):
    """Assigns 0.0 to 1.0 for the Traffic Light system."""
    score = 0.85 
    cs_terms = ['algorithm', 'variable', 'function', 'class', 'complexity', 'data structure', 'binary', 'logic']
    if any(term in raw_sentence.lower() for term in cs_terms):
        score += 0.10
    if any(word in raw_sentence.lower() for word in ['maybe', 'might', 'example']):
        score -= 0.30
    if len(raw_sentence.split()) > 40 or len(raw_sentence.split()) < 3:
        score -= 0.20
    return round(max(0.1, min(1.0, score)), 2)

# --- UPDATED FLASHCARD GENERATION ---
def generate_flashcards_from_file(filepath):
    text = extract_text_from_file(filepath)
    if not text.strip(): 
        return []
    
    flashcards = []
    # STEP 1: Process by lines to catch slide bullet points
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line or len(line) < 5: continue

        # 1. Colon Logic (e.g., "Heuristic: A technique...")
        if ":" in line:
            parts = line.split(":", 1)
            term = parts[0].strip()
            definition = clean_text(parts[1])
            
            # Filter junk and ensure reasonable term length
            if term.lower() not in EXACT_JUNK and 1 <= len(term.split()) <= 6:
                if len(definition) > 5:
                    flashcards.append({
                        "question": f"What is {term}?",
                        "answer": definition,
                        "score": 0.80
                    })
                    continue

        # 2. Regex Logic (e.g., "Sorting is the process...")
        match = re.search(r'^(.+?)\s+(is|are|means|refers to|is defined as)\s+(.+)', line, re.I)
        if match:
            term = match.group(1).strip()
            definition = clean_text(match.group(3))
            
            # Filter junk and check if term is likely a noun phrase
            if term.lower() not in EXACT_JUNK and len(term.split()) <= 6:
                term_doc = nlp(term)
                if any(t.pos_ in ['NOUN', 'PROPN'] for t in term_doc):
                    flashcards.append({
                        "question": f"What is {term}?",
                        "answer": definition,
                        "score": calculate_confidence(term, definition, line)
                    })

    # STEP 2: CS Formula Logic
    formula_matches = re.findall(r'([A-Za-z0-9_]+\s*=\s*[^.\n]+)', text)
    for f in formula_matches:
        if any(op in f for op in ["+", "-", "*", "/", "^"]):
            flashcards.append({
                "question": "Explain this formula/expression:", 
                "answer": f.strip(), 
                "score": 0.90
            })

    # Remove duplicates based on the question text
    unique_results = {c['question'].lower(): c for c in flashcards}.values()
    final_list = list(unique_results)
    random.shuffle(final_list)
    return final_list

# --- ANSWER CHECKING ---
def is_answer_correct(user_answer, correct_answer, threshold=75):
    """Fuzzy logic for comparing user input to stored answers."""
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