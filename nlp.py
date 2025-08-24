import re
import random
import os
from docx import Document
from PyPDF2 import PdfReader
from pptx import Presentation
from PIL import Image
import pytesseract

from collections import Counter

# Utility: Score flashcards
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



# Core: Split into flashcards
def split_into_flashcards(text):
    """Extract flashcards from raw text using smarter rules + regex."""

    flashcards = []
    lines = text.splitlines()

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # -------------------------------
        # 1. Definitions ("X is Y")
        # -------------------------------
        def_match = re.match(r"^(.+?)\s+(is|are|means|refers to)\s+(.+)", line, re.I)
        if def_match:
            subject = def_match.group(1).strip()
            definition = def_match.group(3).strip()
            q = f"What is {subject}?"
            a = definition
            flashcards.append({
                "question": q,
                "answer": a,
                "score": score_flashcard(q, a, "definition")
            })
            continue

        # -------------------------------
        # 2. Headings (titles / bullet points)
        # -------------------------------
        heading_match = re.match(r"^(#+|\d+\.|-)\s*(.+)", line)
        if heading_match:
            topic = heading_match.group(2).strip()
            q = f"Explain {topic}"
            a = f"Key points: {topic}"
            flashcards.append({
                "question": q,
                "answer": a,
                "score": score_flashcard(q, a, "heading")
            })
            continue

        # -------------------------------
        # 3. Formula style (math/science)
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
        # 4. Notes with keywords (why, how, etc.)
        # -------------------------------
        keywords = ["define", "explain", "describe", "why", "how", "advantage", "disadvantage"]
        if any(kw in line.lower() for kw in keywords):
            q = line.strip("?") + "?"
            a = f"Answer: {line}"
            flashcards.append({
                "question": q,
                "answer": a,
                "score": score_flashcard(q, a, "keyword")
            })
            continue

        # -------------------------------
        # 5. General factual sentence → turn into "What does X show?"
        # -------------------------------
        if "tells you" in line.lower() or "shows" in line.lower():
            subject = line.split("tells you")[0].split("shows")[0].strip()
            q = f"What does {subject} show?"
            a = line.split("tells you")[-1].split("shows")[-1].strip()
            flashcards.append({
                "question": q,
                "answer": a,
                "score": score_flashcard(q, a, "general")
            })
            continue

        # -------------------------------
        # 6. Long sentence fallback
        # -------------------------------
        if len(line.split()) > 6 and line.endswith("."):
            q = f"What does this mean: {line.split()[0:5]}..."
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
# Text Extraction
# -------------------------------
def extract_text_from_file(filepath):
    """Extract text from various file types (txt, docx, pdf, pptx, png, jpg)."""
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

    elif ext == ".pptx":
        prs = Presentation(filepath)
        slides_text = []
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    slides_text.append(shape.text)
        text = "\n".join(slides_text)

    elif ext in [".png", ".jpg", ".jpeg"]:
        try:
            img = Image.open(filepath)
            text = pytesseract.image_to_string(img)
        except Exception as e:
            print(f"OCR failed for {filepath}: {e}")
            text = ""

    else:
        # Unsupported formats return empty
        text = ""

    return text


# -------------------------------
# Flashcard Generation
# -------------------------------
def generate_flashcards(text):
    """Generate cleaned flashcards from raw text."""
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
# Entry: From File
# -------------------------------
def generate_flashcards_from_file(filepath):
    """Wrapper: Extract text and generate flashcards."""
    text = extract_text_from_file(filepath)
    if not text.strip():
        return []
    return generate_flashcards(text)
