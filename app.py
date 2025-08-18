from bson import ObjectId
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from nlp import extract_text_from_file, generate_flashcards_from_file, split_into_flashcards
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
from werkzeug.utils import secure_filename
from docx import Document
import os
import fitz  # PyMuPDF
import re
from datetime import datetime

# Environment and DB Setup
load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback_secret')
app.config['UPLOAD_FOLDER'] = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'docx', 'pdf'}

client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"))
db = client['flashcarddb']
users = db['users']
flashcards = db['flashcards']
flashcardsets = db['flashcardsets']
bcrypt = Bcrypt(app)

# Auth routes

@app.route('/')
def welcome():
    return render_template('welcome.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')

        # Check if user already exists
        if users.find_one({'username': username}):
            flash("User already exists!")
            return redirect(url_for('welcome'))

        # Insert user
        result = users.insert_one({'username': username, 'password': password})

        # Auto-login
        session['username'] = username
        session['user_id'] = str(result.inserted_id)

        flash("Welcome to FlashMind!")
        return redirect(url_for('dashboard'))

    return redirect(url_for('welcome'))



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = users.find_one({'username': request.form['username']})
        if user and bcrypt.check_password_hash(user['password'], request.form['password']):
            session['username'] = user['username']
            session['user_id'] = str(user['_id'])
            return redirect(url_for('dashboard'))
        flash("Invalid credentials")
    return redirect(url_for('welcome'))
 


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('welcome'))  # ✅ go back to the welcome modal


# Dashboard
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    sets = list(flashcardsets.find({'user_id': ObjectId(session['user_id'])}))
    return render_template('dashboard.html', sets=sets)

# Create Flashcard Set
@app.route('/create-set', methods=['GET', 'POST'])
def create_set():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        flashcardsets.insert_one({
            'user_id': ObjectId(session['user_id']),
            'name': request.form['title'],
            'created_at': datetime.utcnow()
        })
        flash("Set created!")
        return redirect(url_for('dashboard'))
    return render_template('create_set.html')

# Create Flashcard Manually
@app.route('/create-flashcard', methods=['GET', 'POST'])
def create_flashcard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = ObjectId(session['user_id'])
    sets = list(flashcardsets.find({'user_id': user_id}))

    if request.method == 'POST':
        set_id = request.form['flashcard_set_id']
        new_card = {
            "question": request.form['question'],
            "answer": request.form['answer'],
            "score": 1.0,  # default score
            "created_at": datetime.utcnow()
        }

        # ✅ Push card into the set instead of separate collection
        flashcardsets.update_one(
            {"_id": ObjectId(set_id)},
            {"$push": {"flashcards": new_card}}
        )

        flash('Flashcard created!')
        return redirect(url_for('view_set', set_id=set_id))

    return render_template('create_flashcards.html', flashcard_sets=sets)


# View Set
@app.route('/set/<set_id>')
def view_set(set_id):
    cards = list(flashcards.find({'set_id': ObjectId(set_id)}))
    set_data = flashcardsets.find_one({'_id': ObjectId(set_id)})
    return render_template('view_set.html', set_data=set_data, flashcards=cards)


def generate_flashcards_from_file(filepath):
    text = extract_text_from_file(filepath)
    flashcards = split_into_flashcards(text)
    return flashcards

# Upload Notes Page
@app.route('/upload_notes_ajax/<set_id>', methods=['POST'])
def upload_notes_ajax(set_id):
    if 'notes_file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['notes_file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # Call your existing AI / flashcard generation logic here
    flashcards = generate_flashcards_from_file(filepath)  
    # Should return list of (question, answer) tuples

    # Return JSON so dashboard can render it live
    return jsonify({
        "flashcards": [{"question": q, "answer": a} for q, a in flashcards]
    })


# File utilities
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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

# Simple NLP logic
def split_into_flashcards(text):
    flashcards = []
    sentences = re.split(r'\. |\? |\! ', text)
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence.split()) >= 5:
            question = f"What is {sentence.split(' ')[0].lower()}?"
            flashcards.append((question, sentence))
    return flashcards

# Preview Generated Flashcards
@app.route('/preview-generated/<filename>')
def preview_generated_flashcards(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    text = extract_text_from_file(filepath)
    generated = split_into_flashcards(text)
    return render_template('preview_generated.html', flashcards=generated)

# Save Flashcards to DB
@app.route("/save_generated_flashcards", methods=["POST"])
def save_generated_flashcards():
    if "user_id" not in session:
        return redirect(url_for("login"))

    set_name = request.form.get("set_name")
    questions = request.form.getlist("questions")
    answers = request.form.getlist("answers")
    scores = request.form.getlist("scores")

    flashcards = []
    for q, a, s in zip(questions, answers, scores):
        flashcards.append({
            "question": q,
            "answer": a,
            "score": float(s) if s else 0.0,
            "created_at": datetime.utcnow()
        })

    # ✅ Instead of creating a new set every time, append to existing
    existing_set = flashcardsets.find_one({
        "user_id": ObjectId(session["user_id"]),
        "name": set_name
    })

    if existing_set:
        flashcardsets.update_one(
            {"_id": existing_set["_id"]},
            {"$push": {"flashcards": {"$each": flashcards}}}
        )
    else:
        flashcardsets.insert_one({
            "user_id": ObjectId(session["user_id"]),
            "name": set_name,
            "flashcards": flashcards,
            "created_at": datetime.utcnow()
        })

    flash("Flashcards saved successfully!", "success")
    return redirect(url_for("dashboard"))


# Review Flashcards
@app.route("/review/<set_id>")
def review_flashcards(set_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    flashcard_set = flashcardsets.find_one({"_id": ObjectId(set_id)})
    if not flashcard_set:
        flash("Flashcard set not found.", "danger")
        return redirect(url_for("dashboard"))

    # Fallback: if no "flashcards" field exists, give an empty list
    flashcards_list = flashcard_set.get("flashcards", [])

    return render_template("review_flashcards.html", 
                           flashcard_set=flashcard_set, 
                           flashcards=flashcards_list)


@app.route('/choose_review')
def choose_review():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = ObjectId(session['user_id'])
    sets = list(flashcardsets.find({'user_id': user_id}))
    return render_template('choose_review.html', sets=sets)

@app.route('/set/<set_id>')
def view_set(set_id):
    set_data = flashcardsets.find_one({'_id': ObjectId(set_id)})
    if not set_data:
        flash("Set not found", "danger")
        return redirect(url_for("dashboard"))

    # Pull cards directly from the embedded array
    cards = set_data.get("flashcards", [])

    return render_template('view_set.html', set_data=set_data, flashcards=cards)



# Main
if __name__ == '__main__':
    app.run(debug=True)
