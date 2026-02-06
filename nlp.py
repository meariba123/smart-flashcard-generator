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

# --- IMPROVED FILE EXTRACTION ---
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
                    # Improved check for text in shapes and tables
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

# --- CS-SPECIFIC SCORING (For Traffic Lights) ---
def calculate_confidence(question, answer, raw_sentence):
    """Assigns 0.0 to 1.0 for the Traffic Light system."""
    score = 0.85 # Standard start
    
    cs_terms = ['algorithm', 'variable', 'function', 'class', 'complexity', 'data structure', 'binary', 'complexity']
    if any(term in raw_sentence.lower() for term in cs_terms):
        score += 0.10

    if any(word in raw_sentence.lower() for word in ['maybe', 'might', 'example', 'etc']):
        score -= 0.30
    
    if len(raw_sentence.split()) > 40 or len(raw_sentence.split()) < 3:
        score -= 0.20

    return round(max(0.1, min(1.0, score)), 2)

# --- IMPROVED FLASHCARD GENERATION ---
def generate_flashcards_from_file(filepath):
    text = extract_text_from_file(filepath)
    if not text.strip(): 
        return []
    
    doc = nlp(text)
    flashcards = []
    
    # Process by lines first to catch slide bullet points
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line: continue

        # 1. PPTX Bullet Point Logic (Term: Definition)
        if ":" in line and len(line.split(":")[0].split()) <= 5:
            parts = line.split(":", 1)
            q = f"What is {parts[0].strip()}?"
            a = parts[1].strip()
            if len(a) > 3:
                flashcards.append({"question": q, "answer": a, "score": 0.80})
                continue

        # 2. Definition Logic (Sentence Based)
        match = re.search(r'^(.+?)\s+(is|are|means|refers to|is defined as)\s+(.+)', line, re.I)
        if match:
            term = match.group(1).strip()
            definition = match.group(3).strip()
            if len(term.split()) <= 6: # Ensure the "What is..." part isn't a whole paragraph
                q = f"What is {term}?"
                a = definition
                conf = calculate_confidence(q, a, line)
                flashcards.append({"question": q, "answer": a, "score": conf})

    # 3. CS Formula Logic
    if "=" in text:
        formula_matches = re.findall(r'([A-Za-z0-9_]+\s*=\s*[^.\n]+)', text)
        for f in formula_matches:
            if any(op in f for op in ["+", "-", "*", "/", "^"]):
                flashcards.append({"question": "Explain this formula/expression:", "answer": f.strip(), "score": 0.90})

    # Shuffle for variety
    random.shuffle(flashcards)
    return flashcards

# --- ANSWER CHECKING ---
def is_answer_correct(user_answer, correct_answer, threshold=75):
    user_answer = user_answer.lower().strip()
    correct_answer = correct_answer.lower().strip()
    
    similarity = fuzz.ratio(user_answer, correct_answer)
    if similarity >= threshold:
        return True
        
    user_keywords = set(user_answer.split())
    correct_keywords = set(correct_answer.split())
    if len(correct_keywords) > 0:
        overlap = len(user_keywords & correct_keywords) / len(correct_keywords)
        if overlap > 0.6: 
            return True
            
    return False