# nlp.py
import re
import fitz  # PyMuPDF
from docx import Document

# Extract text from different file types
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

# 🔹 Simple baseline NLP (can be refined later)
def split_into_flashcards(text):
    flashcards = []
    sentences = re.split(r'\. |\? |\! ', text)
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence.split()) >= 5:
            # Very naive question: first word focus
            question = f"What is {sentence.split(' ')[0].lower()}?"
            flashcards.append((question, sentence))
    return flashcards

# 🔹 A wrapper function
def generate_flashcards_from_file(filepath):
    text = extract_text_from_file(filepath)
    return split_into_flashcards(text)
