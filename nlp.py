import re
import random
import os
from docx import Document
from PyPDF2 import PdfReader
from pptx import Presentation
import pytesseract
from PIL import Image

# If using Windows, set the path to your installed Tesseract:
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


# -------------------------------
# Utility: Score flashcards
# -------------------------------
def score_flashcard(question, answer, source="general"):
    """Score flashcards so stronger ones appear first."""
    base_score = 1

    if source == "heading":
        base_score += 3
    elif source == "definition":
        base_score += 2
    elif source == "formula":
        base_score += 2
    elif source == "keyword":
        base_score += 2

    # Longer answers are usually richer
    if len(answer.split()) > 5:
        base_score += 1

    return base_score


# -------------------------------
# Core: Split into flashcards
# -------------------------------
def split_into_flashcards(text):
    """Extract flashcards from raw text using rules + regex."""

    flashcards = []
    lines = text.splitlines()

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # -------------------------------
        # 1. Heading-based Q&A
        # -------------------------------
        heading_match = re.match(r"^(#+|\d+\.|-)\s*(.+)", line)
        if heading_match:
            q = f"Explain {heading_match.group(2).strip()}"
            a = f"Key points about {heading_match.group(2).strip()}."
            flashcards.append({
                "question": q,
                "answer": a,
                "score": score_flashcard(q, a, "heading")
            })
            continue

        # -------------------------------
        # 2. Definition style ("X is Y")
        # -------------------------------
        def_match = re.match(r"^(.+?)\s+(is|are|means|refers to)\s+(.+)", line, re.I)
        if def_match:
            subject = def_match.group(1).strip()
            q = f"What is {subject}?"
            a = def_match.group(3).strip()
            flashcards.append({
                "question": q,
                "answer": a,
                "score": score_flashcard(q, a, "definition")
            })
            continue

        # -------------------------------
        # 3. Formula style
        # -------------------------------
        if "=" in line and any(sym in line for sym in ["+", "-", "*", "/", "^"]):
            q = "What does this formula represent?"
            a = line
            flashcards.append({
                "question": q,
                "answer": a,
                "score": score_flashcard(q, a, "formula")
            })
            continue

        # -------------------------------
        # 4. Keyword-based extraction
        # -------------------------------
        keywords = ["define", "explain", "describe", "why", "how", "advantage", "disadvantage"]
        if any(kw in line.lower() for kw in keywords):
            q = line.strip("?") + "?"
            a = "Expand on this idea: " + line
            flashcards.append({
                "question": q,
                "answer": a,
                "score": score_flashcard(q, a, "keyword")
            })
            continue

        # -------------------------------
        # 5. Smarter fallback
        # -------------------------------
        # Long sentence fallback (improved)
        if len(line.split()) > 6 and line.endswith("."):
            subject = " ".join(line.split()[:6])  # first 6 words as context
            q = f"In context of '{subject}...', what does this mean?"
            a = line
            flashcards.append({
                "question": q,
                "answer": a,
                "score": score_flashcard(q, a, "general")
            })


    # Shuffle for variety, then sort by score
    random.shuffle(flashcards)
    flashcards.sort(key=lambda x: x["score"], reverse=True)

    return flashcards


# -------------------------------
# File text extraction
# -------------------------------
def extract_text_from_file(filepath):
    """Extract text from various file types including OCR for images."""
    ext = os.path.splitext(filepath)[1].lower()
    text = ""

    if ext == ".txt":
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()

    elif ext == ".docx":
        doc = Document(filepath)
        text = "\n".join([para.text for para in doc.paragraphs])

    elif ext == ".pdf":
        reader = PdfReader(filepath)
        pages = [page.extract_text() or "" for page in reader.pages]
        text = "\n".join(pages)

    elif ext in [".png", ".jpg", ".jpeg"]:
        # OCR image → text
        img = Image.open(filepath)
        text = pytesseract.image_to_string(img)

    elif ext == ".pptx":
        prs = Presentation(filepath)
        text_runs = []
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    text_runs.append(shape.text)
        text = "\n".join(text_runs)

    else:
        text = ""

    return text


# -------------------------------
# Generate flashcards
# -------------------------------
def generate_flashcards(text):
    flashcards = split_into_flashcards(text)
    clean_cards = []
    for fc in flashcards:
        q = fc.get("question", "").strip()
        a = fc.get("answer", "").strip()
        if q:
            if not a:
                a = "Answer not available — expand with your own notes."
            clean_cards.append({
                "question": q,
                "answer": a,
                "score": fc.get("score", 0)
            })
    return clean_cards


# -------------------------------
# Entry: From file
# -------------------------------
def generate_flashcards_from_file(filepath):
    """Wrapper: Extract text and generate flashcards."""
    text = extract_text_from_file(filepath)
    if not text.strip():
        return []
    return generate_flashcards(text)
