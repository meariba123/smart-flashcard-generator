import re #im using this library as it detects pattern in text such as definitions or headings 
import random #this is used for shuffling the flashcards in different order at random 
import os #this checks the file file extensions
from docx import Document #this reads the word documents when user imports them to file (.docx)
from PyPDF2 import PdfReader #this reads pdf readings imported by user 
from pptx import Presentation #reads powerpoint slides imported by user 
import pytesseract #this library and the one below are used together for OCR. (extracting text from images)
from PIL import Image #to detect image readings imported by user such as .png or.jpg

# If using Windows, set the path to your installed Tesseract:
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


# Utility: Score flashcards
#the purpose of this function "score flashcards" is to assign a "priority score" to a flashcard.

#commenting on this later!!
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


#splitting into flashcards
#the purpose of this function is to break raw text into Q&A flashcards.
def split_into_flashcards(text):
    """Extract flashcards from raw text using rules + regex."""

    flashcards = [] #this is an empty list where we will store generated flashcards. 
    lines = text.splitlines() #splits into text into individual lines (each sentence/paragraph line)

    #this loops through every line in the text.
    for line in lines: 
        line = line.strip() #line.strip() removes leading/trailing spaces.
        if not line: #if line is empty after stripping - skip it.
            continue

        
        #checks if the line looks like a heading (#, a number like 1., or a dash -)
        heading_match = re.match(r"^(#+|\d+\.|-)\s*(.+)", line)
        if heading_match: #if yes, it creates a flashcard:
            q = f"Explain {heading_match.group(2).strip()}" #question = "Explain {heading text}"
            a = f"Key points about {heading_match.group(2).strip()}." #answer ="Key points about {heading text}"
            #calls score_flashcard() to assign a score
            flashcards.append({
                "question": q,
                "answer": a,
                "score": score_flashcard(q, a, "heading")
            })
            continue #then continue skips to the next line.

        # 2. Definition style ("X is Y")
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

        
        # 3. Formula style
        if "=" in line and any(sym in line for sym in ["+", "-", "*", "/", "^"]):
            q = "What does this formula represent?"
            a = line
            flashcards.append({
                "question": q,
                "answer": a,
                "score": score_flashcard(q, a, "formula")
            })
            continue

        # 4. Keyword-based extraction
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

        # 5. Smarter fallback
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



# File text extraction
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


# Generate flashcards
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


# Entry: From file
def generate_flashcards_from_file(filepath):
    """Wrapper: Extract text and generate flashcards."""
    text = extract_text_from_file(filepath)
    if not text.strip():
        return []
    return generate_flashcards(text)
