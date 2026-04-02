import re
import random
import os
import spacy
from docx import Document
from PyPDF2 import PdfReader
from pptx import Presentation
import pytesseract
from rapidfuzz import fuzz
from PIL import Image, ImageDraw, ImageFont
import textwrap
from deep_translator import GoogleTranslator  # <--- New Import

# LOAD SPACY
try:
    nlp = spacy.load("en_core_web_sm")
except:
    os.system("python -m spacy download en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# CONSTANTS
EXACT_JUNK = {'this', 'that', 'it', 'they', 'there', 'what', 'which', 'who', 'example', 'examples'}
URL_PATTERN = r'(https?://\S+|www\.\S+|\S+\.com/\S+|\S+\.be/\S+)'
PREFIX_JUNK = r'^(e\.g\.|i\.e\.|etc|example:|note:)\s+'
MAX_VISUALS = 3

# --- NEW TRANSLATION HELPER ---
def translate_if_needed(text, target_lang):
    if not text or target_lang == 'en':
        return text
    try:
        # Translates from English (auto-detected) to your target (e.g., 'es')
        return GoogleTranslator(source='auto', target=target_lang).translate(text)
    except Exception as e:
        print(f"Translation Error: {e}")
        return text

# CLEANING FUNCTIONS
def clean_term(term):
    term = re.sub(PREFIX_JUNK, '', term, flags=re.IGNORECASE)
    term = re.sub(URL_PATTERN, '', term)
    return term.strip().capitalize()

def clean_text(text):
    text = re.sub(URL_PATTERN, '', text)
    text = re.sub(r'\(.*?\)', '', text)
    text = text.replace(' - ', ' ').replace(' : ', ' ')
    return text.strip()

def is_valid_term(term):
    if not term or len(term) < 3: return False
    if term.lower() in EXACT_JUNK: return False
    if not re.search(r'[a-zA-Z]', term): return False
    return True

# VISUAL EXPLANATION
def generate_visual_explanation(term):
    try:
        safe_term = re.sub(r'[^a-zA-Z0-9_]', '_', term.strip())
        img = Image.new("RGB", (900, 450), "white")
        draw = ImageDraw.Draw(img)
        try:
            font_title = ImageFont.truetype("arial.ttf", 42)
            font_body = ImageFont.truetype("arial.ttf", 22)
        except:
            font_title = ImageFont.load_default()
            font_body = ImageFont.load_default()

        draw.text((40, 20), term, fill="black", font=font_title)
        os.makedirs("static/generated_images", exist_ok=True)
        image_path = f"static/generated_images/{safe_term}.png"
        img.save(image_path)
        return f"generated_images/{safe_term}.png"
    except:
        return None

# TEXT EXTRACTION
def extract_text_from_file(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    text = ""
    try:
        if ext == ".txt":
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f: text = f.read()
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
        print(f"Extraction Error: {e}")
    return text

# --- FLASHCARD GENERATION WITH TRANSLATION ---
def generate_flashcards_from_file(filepath, language='en'):
    print(f"DEBUG: Generating flashcards in language: {language}")
    ext = os.path.splitext(filepath)[1].lower()
    flashcards = []

    lang_config = {
        'es': {"prefix": "¿Qué es", "suffix": "?"},
        'en': {"prefix": "What is", "suffix": "?"}
    }
    l = lang_config.get(language, lang_config['en'])

    if ext == ".pptx":
        prs = Presentation(filepath)
        for slide in prs.slides:
            title, content = "", []
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    if not title: title = shape.text.strip()
                    else: content.append(shape.text.strip())
            
            if is_valid_term(title) and content:
                # TRANSLATE HERE
                final_term = translate_if_needed(title, language)
                final_content = translate_if_needed(" ".join(content), language)

                flashcards.append({
                    "question": f"{l['prefix']} {final_term}{l['suffix']}",
                    "answer": final_content,
                    "visual_explanation": None,
                    "score": 0.9
                })
    else:
        text = extract_text_from_file(filepath)
        for line in text.split('\n'):
            if ":" in line:
                parts = line.split(":", 1)
                term = clean_term(parts[0])
                definition = clean_text(parts[1])
                if is_valid_term(term) and len(definition) > 10:
                    # TRANSLATE HERE
                    final_term = translate_if_needed(term, language)
                    final_content = translate_if_needed(definition, language)

                    flashcards.append({
                        "question": f"{l['prefix']} {final_term}{l['suffix']}",
                        "answer": final_content,
                        "visual_explanation": None,
                        "score": 0.8
                    })

    # Deduplicate and finalize
    unique = {c["question"].lower(): c for c in flashcards}
    flashcards = list(unique.values())

    for card in flashcards[:MAX_VISUALS]:
        # Generate visual using the translated term
        clean_q = card["question"].replace(l['prefix'], "").replace(l['suffix'], "").strip()
        card["visual_explanation"] = generate_visual_explanation(clean_q)

    random.shuffle(flashcards)
    return flashcards

def is_answer_correct(user_answer, correct_answer, threshold=75):
    user_answer, correct_answer = user_answer.lower().strip(), correct_answer.lower().strip()
    return fuzz.ratio(user_answer, correct_answer) >= threshold