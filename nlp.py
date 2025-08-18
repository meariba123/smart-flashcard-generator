# nlp.py (refined)
import re
import fitz
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
    doc = Document(filepath)
    content = []
    for para in doc.paragraphs:
        style = para.style.name.lower()
        text = para.text.strip()
        if not text:
            continue
        if "heading" in style:
            content.append(("HEADING", text))
        else:
            content.append(("TEXT", text))
    return content

def extract_text_from_pdf(filepath):
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
                        if font_size >= 14:  
                            content.append(("HEADING", text))
                        else:
                            content.append(("TEXT", text))
    return content


# ---------- Scoring ----------
def score_flashcard(question, answer, source="fallback"):
    score = 0.5  # base

    # By source
    if source == "heading": score += 0.4
    elif source == "definition": score += 0.5
    elif source == "formula": score += 0.3
    else: score -= 0.2

    # Answer length (ideal 10–50 words)
    word_count = len(answer.split())
    if 10 <= word_count <= 50:
        score += 0.2
    elif word_count < 5 or word_count > 80:
        score -= 0.2

    # Keyword hints
    if any(kw in answer.lower() for kw in ["is", "are", "refers to", "defined"]):
        score += 0.1

    return round(max(0, min(1, score)), 2)


# ---------- Flashcard Generation ----------
def split_into_flashcards(content):
    flashcards = []

    # Structured (list of tuples)
    if isinstance(content, list):
        current_heading = None
        for kind, text in content:
            if kind == "HEADING":
                current_heading = text
            elif kind == "TEXT" and current_heading:
                q = f"What is {current_heading}?"
                a = text
                flashcards.append({
                    "question": q,
                    "answer": a,
                    "score": score_flashcard(q, a, source="heading")
                })
                current_heading = None
    else:
        text = content

        # Definitions
        definition_pattern = re.compile(r'(\b[A-Z][a-zA-Z0-9 ]+\b) (is|are|refers to|means) (.+?)(\.|\n)', re.IGNORECASE)
        for match in definition_pattern.finditer(text):
            term = match.group(1).strip()
            definition = match.group(3).strip()
            q = f"What is {term}?"
            a = definition
            flashcards.append({
                "question": q,
                "answer": a,
                "score": score_flashcard(q, a, source="definition")
            })

        # Formulas
        formula_pattern = re.compile(r'([A-Za-z0-9\(\)\^\*\+\-/ ]+)=([A-Za-z0-9\(\)\^\*\+\-/ ]+)')
        for match in formula_pattern.finditer(text):
            formula = match.group(0).strip()
            lhs = match.group(1).strip()
            q = f"What is the formula for {lhs}?"
            a = formula
            flashcards.append({
                "question": q,
                "answer": a,
                "score": score_flashcard(q, a, source="formula")
            })

        # Fallback sentences
        sentences = re.split(r'\. |\? |\! ', text)
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence.split()) >= 6:
                q = f"Explain: {sentence.split()[0:3]}..."
                a = sentence
                flashcards.append({
                    "question": q,
                    "answer": a,
                    "score": score_flashcard(q, a, source="fallback")
                })

    # Sort by score (best first)
    return sorted(flashcards, key=lambda x: x["score"], reverse=True)


def generate_flashcards_from_file(filepath):
    content = extract_text_from_file(filepath)
    return split_into_flashcards(content)
