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
        return extract_text_from_docx(filepath)
    elif ext == 'pdf':
        return extract_text_from_pdf(filepath)
    return ""

def extract_text_from_docx(filepath):
    """
    Extract headings + text from a .docx file.
    """
    doc = Document(filepath)
    content = []
    for para in doc.paragraphs:
        style = para.style.name.lower()
        text = para.text.strip()
        if not text:
            continue
        if "heading" in style:  # treat as question
            content.append(("HEADING", text))
        else:
            content.append(("TEXT", text))
    return content

def extract_text_from_pdf(filepath):
    """
    Extract headings (large fonts) + body text from PDF.
    """
    content = []
    with fitz.open(filepath) as doc:
        for page in doc:
            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                if "lines" in block:
                    for line in block["lines"]:
                        text = " ".join([span["text"] for span in line["spans"]]).strip()
                        if not text:
                            continue
                        font_size = line["spans"][0]["size"]
                        if font_size >= 14:  # heuristic: bigger text = heading
                            content.append(("HEADING", text))
                        else:
                            content.append(("TEXT", text))
    return content

# ---------- Flashcard Generation ----------
def split_into_flashcards(text_or_content):
    flashcards = []

    # If content is structured (list of tuples), handle headings
    if isinstance(text_or_content, list):
        current_heading = None
        for kind, text in text_or_content:
            if kind == "HEADING":
                current_heading = text
            elif kind == "TEXT" and current_heading:
                q = f"What is {current_heading}?"
                flashcards.append((q, text))
                current_heading = None  # reset after using once
    else:
        # Plain text fallback
        text = text_or_content

        # 1️⃣ Definitions
        definition_pattern = re.compile(r'(\b[A-Z][a-zA-Z0-9 ]+\b) (is|are|refers to|means) (.+?)(\.|\n)', re.IGNORECASE)
        for match in definition_pattern.finditer(text):
            term = match.group(1).strip()
            definition = match.group(3).strip()
            question = f"What is {term}?"
            flashcards.append((question, definition))

        # 2️⃣ Formulas
        formula_pattern = re.compile(r'([A-Za-z0-9\(\)\^\*\+\-/ ]+)=([A-Za-z0-9\(\)\^\*\+\-/ ]+)')
        for match in formula_pattern.finditer(text):
            formula = match.group(0).strip()
            lhs = match.group(1).strip()
            question = f"What is the formula for {lhs}?"
            flashcards.append((question, formula))

        # 3️⃣ Sentences fallback
        sentences = re.split(r'\. |\? |\! ', text)
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence.split()) >= 6 and not any(sentence in ans for _, ans in flashcards):
                first_word = sentence.split()[0].lower()
                question = f"What is {first_word}?"
                flashcards.append((question, sentence))

    return flashcards

# Wrapper
def generate_flashcards_from_file(filepath):
    content = extract_text_from_file(filepath)
    return split_into_flashcards(content)
