# nlp.py
import re
import fitz  # PyMuPDF
from docx import Document

# ---------- File Extraction ----------
def extract_text_from_file(filepath):
    ext = filepath.rsplit('.', 1)[-1].lower()
    if ext == 'txt':
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    elif ext == 'docx':
        doc = Document(filepath)
        return "\n".join([para.text for para in doc.paragraphs])
    elif ext == 'pdf':
        return extract_text_from_pdf(filepath)
    return ""

def extract_text_from_pdf(filepath):
    text = ""
    with fitz.open(filepath) as doc:
        for page in doc:
            text += page.get_text()
    return text

# ---------- Flashcard Generation ----------
def split_into_flashcards(text):
    flashcards = []

    # 1️⃣ Capture definitions like "X is Y" or "X refers to Y"
    definition_pattern = re.compile(r'(\b[A-Z][a-zA-Z0-9 ]+\b) (is|are|refers to|means) (.+?)(\.|\n)', re.IGNORECASE)
    for match in definition_pattern.finditer(text):
        term = match.group(1).strip()
        definition = match.group(3).strip()
        question = f"What is {term}?"
        flashcards.append((question, definition))

    # 2️⃣ Capture formulas (something = something)
    formula_pattern = re.compile(r'([A-Za-z0-9\(\)\^\*\+\-/ ]+)=([A-Za-z0-9\(\)\^\*\+\-/ ]+)')
    for match in formula_pattern.finditer(text):
        formula = match.group(0).strip()
        lhs = match.group(1).strip()
        question = f"What is the formula for {lhs}?"
        flashcards.append((question, formula))

    # 3️⃣ General sentences (fallback if no match)
    sentences = re.split(r'\. |\? |\! ', text)
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence.split()) >= 6 and not any(sentence in ans for _, ans in flashcards):
            # Build a simple question from the first noun-like word
            first_word = sentence.split()[0].lower()
            question = f"What is {first_word}?"
            flashcards.append((question, sentence))

    return flashcards


# Wrapper
def generate_flashcards_from_file(filepath):
    text = extract_text_from_file(filepath)
    return split_into_flashcards(text)
