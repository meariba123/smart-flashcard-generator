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

# --- FILE EXTRACTION (Keeping your OCR & PowerPoint logic) ---
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
            text = "\n".join([shape.text for slide in prs.slides for shape in slide.shapes if hasattr(shape, "text")])
    except Exception as e:
        print(f"Error extracting text: {e}")
    return text

# --- CS-SPECIFIC SCORING (For Traffic Lights) ---
def calculate_confidence(question, answer, raw_sentence):
    """Assigns 0.0 to 1.0 for the Traffic Light system."""
    score = 0.90 # Start high (Green)
    
    # CS Keywords boost confidence
    cs_terms = ['algorithm', 'variable', 'function', 'class', 'complexity', 'data structure', 'binary']
    if any(term in raw_sentence.lower() for term in cs_terms):
        score += 0.05

    # Vague language lowers confidence (Amber/Red)
    if any(word in raw_sentence.lower() for word in ['maybe', 'might', 'example', 'etc']):
        score -= 0.30
    
    # Length checks (Noisy text)
    if len(raw_sentence.split()) > 35 or len(raw_sentence.split()) < 4:
        score -= 0.20

    return round(max(0.1, min(1.0, score)), 2)

# --- FLASHCARD GENERATION ---
def generate_flashcards_from_file(filepath):
    text = extract_text_from_file(filepath)
    if not text.strip(): return []
    
    doc = nlp(text)
    flashcards = []
    
    for sent in doc.sents:
        line = sent.text.strip()
        
        # 1. Definition Logic (CS Focused)
        # Matches: "Binary Search is an algorithm..."
        match = re.search(r'^(.+?)\s+(is|are|means|refers to|is defined as)\s+(.+)', line, re.I)
        if match:
            q = f"What is {match.group(1).strip()}?"
            a = match.group(3).strip()
            conf = calculate_confidence(q, a, line)
            flashcards.append({"question": q, "answer": a, "score": conf})
            continue

        # 2. Formula Logic (CS Math)
        if "=" in line and any(sym in line for sym in ["+", "-", "*", "/", "^"]):
            q = "What does this CS-related formula represent?"
            a = line
            flashcards.append({"question": q, "answer": a, "score": 0.85})

    # Shuffle for variety
    random.shuffle(flashcards)
    return flashcards

# --- ANSWER CHECKING (Fuzzy Logic) ---
def is_answer_correct(user_answer, correct_answer, threshold=75):
    user_answer = user_answer.lower().strip()
    correct_answer = correct_answer.lower().strip()
    
    # Fuzzy match + Keyword overlap
    similarity = fuzz.ratio(user_answer, correct_answer)
    if similarity >= threshold:
        return True
        
    user_keywords = set(user_answer.split())
    correct_keywords = set(correct_answer.split())
    if len(correct_keywords) > 0:
        overlap = len(user_keywords & correct_keywords) / len(correct_keywords)
        if overlap > 0.6: # 60% of keywords present
            return True
            
    return False