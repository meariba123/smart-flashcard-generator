# app.py
from bson import ObjectId
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, current_app
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
from werkzeug.utils import secure_filename
from datetime import datetime
import os

# Import advanced NLP pipeline (keep your existing nlp.py)
from nlp import extract_text_from_file, generate_flashcards_from_file, is_answer_correct

# Import blueprint that contains progress routes
from user_progress import progress_bp

# Environment + Flask Setup
load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback_secret')
app.config['UPLOAD_FOLDER'] = 'uploads'
ALLOWED_EXTENSIONS = {'txt','doc','docx','pdf','ppt','pptx','png','jpg','jpeg'}
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# MongoDB Setup (same DB name you used)
client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"))
db = client['flashcarddb']   # keep same name 'flashcarddb'
users = db['users']
flashcards = db['flashcards']
flashcardsets = db['flashcardsets']
progress = db['progress']

# Expose db for blueprints to use current_app.db
app.db = db

bcrypt = Bcrypt(app)

# Register blueprint (no prefix so endpoints are global, matching existing frontend)
app.register_blueprint(progress_bp)


# ------------------ Auth Routes ------------------
@app.route('/')
def welcome():
    return render_template('welcome.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')

        # Check if user exists
        if users.find_one({'username': username}):
            flash("User already exists!")
            return redirect(url_for('welcome'))

        # Create user
        result = users.insert_one({'username': username, 'password': password})

        # Auto login
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
    return redirect(url_for('welcome'))


# ------------------ Dashboard ------------------
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    sets = list(flashcardsets.find({'user_id': ObjectId(session['user_id'])}))
    return render_template('dashboard.html', sets=sets)


# ------------------ Create Flashcard Set ------------------
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


# ------------------ Create Flashcard Manually ------------------
@app.route('/create-flashcard', methods=['GET', 'POST'])
def create_flashcard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = ObjectId(session['user_id'])
    sets = list(flashcardsets.find({'user_id': user_id}))
    if request.method == 'POST':
        set_id = request.form['flashcard_set_id']
        flashcards.insert_one({
            'user_id': user_id,
            'set_id': ObjectId(set_id),
            'question': request.form['question'],
            'answer': request.form['answer'],
            'created_at': datetime.utcnow()
        })
        flash('Flashcard created!')
        return redirect(url_for('view_set', set_id=set_id))
    return render_template('create_flashcards.html', flashcard_sets=sets)


# ------------------ View Flashcard Set ------------------
@app.route('/set/<set_id>')
def view_set(set_id):
    cards = list(flashcards.find({'set_id': ObjectId(set_id)}))
    set_data = flashcardsets.find_one({'_id': ObjectId(set_id)})
    return render_template('view_set.html', set_data=set_data, flashcards=cards)


# ------------------ Upload Notes (AJAX) ------------------
@app.route('/upload_notes_ajax', methods=['POST'])
def upload_notes_ajax():
    if 'notes_file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['notes_file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # Generate flashcards via NLP
    flashcards_generated = generate_flashcards_from_file(filepath)

    # Store temporarily in session
    session['temp_generated'] = [
        {"question": c.get("question",""), "answer": c.get("answer",""), "score": c.get("score", 0)}
        for c in flashcards_generated
    ]
    session['temp_filename'] = filename

    return jsonify({"ok": True, "redirect": url_for('review_temp')})

@app.route('/review-temp')
def review_temp():
    temp = session.get('temp_generated')
    if not temp:
        flash('No generated flashcards to review yet.', 'warning')
        return redirect(url_for('dashboard'))

    flashcard_set = {"name": "Unsaved Generated Set"}
    return render_template(
        'review_flashcards.html',
        flashcard_set=flashcard_set,
        flashcards=temp,
        temp_mode=True
    )


# ------------------ Preview Generated Flashcards ------------------
@app.route('/preview-generated/<filename>')
def preview_generated_flashcards(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    generated = generate_flashcards_from_file(filepath)
    return render_template('preview_generated.html', flashcards=generated)


# ------------------ Save Generated Flashcards ------------------
@app.route('/save-generated-flashcards', methods=['POST'])
def save_generated_flashcards():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = ObjectId(session['user_id'])
    questions = request.form.getlist('questions')
    answers = request.form.getlist('answers')
    set_name = request.form.get('set_name')

    existing_set = flashcardsets.find_one({'user_id': user_id, 'name': set_name})
    if existing_set:
        set_id = existing_set['_id']
    else:
        set_id = flashcardsets.insert_one({
            'user_id': user_id,
            'name': set_name,
            'created_at': datetime.utcnow()
        }).inserted_id

    for q, a in zip(questions, answers):
        flashcards.insert_one({
            'user_id': user_id,
            'set_id': set_id,
            'question': q,
            'answer': a,
            'created_at': datetime.utcnow()
        })

    session.pop('temp_generated', None)
    session.pop('temp_filename', None)

    flash('Flashcards saved successfully!', 'success')
    return redirect(url_for('dashboard'))


# ------------------ Review Flashcards ------------------
@app.route("/review/<set_id>")
def review_flashcards(set_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = ObjectId(session["user_id"])
    db = current_app.db  # ✅ correctly get the MongoDB connection

    flashcard_set = db.flashcardsets.find_one({"_id": ObjectId(set_id), "user_id": user_id})
    if not flashcard_set:
        return "Set not found", 404

    # ✅ Fix: Convert ObjectIds to strings
    flashcards = list(db.flashcards.find({"set_id": ObjectId(set_id), "user_id": user_id}))
    for card in flashcards:
        card["_id"] = str(card["_id"])
        card["set_id"] = str(card["set_id"])

    return render_template(
        "review_flashcards.html",
        flashcard_set=flashcard_set,
        flashcards=flashcards
    )


@app.route('/choose_review')
def choose_review():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = ObjectId(session['user_id'])
    sets = list(flashcardsets.find({'user_id': user_id}))
    return render_template('choose_review.html', sets=sets)


# ------------------ Check Answer (AJAX) ------------------
@app.route("/check_answer", methods=["POST"])
def check_answer():
    data = request.get_json()
    user_answer = data.get("user_answer", "")
    correct_answer = data.get("correct_answer", "")

    if is_answer_correct(user_answer, correct_answer):
        return jsonify({"correct": True})
    else:
        return jsonify({"correct": False, "correct_answer": correct_answer})


# ------------------ File Utility ------------------
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ------------------ Main ------------------
if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
