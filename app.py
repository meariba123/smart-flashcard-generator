# app.py
from bson import ObjectId
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
from werkzeug.utils import secure_filename
from datetime import datetime
import os

# Import advanced NLP pipeline
from nlp import extract_text_from_file, generate_flashcards_from_file

# ------------------ Environment + Flask Setup ------------------
load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback_secret')
app.config['UPLOAD_FOLDER'] = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'docx', 'pdf'}

# ------------------ MongoDB Setup ------------------
client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"))
db = client['flashcarddb']
users = db['users']
flashcards = db['flashcards']
flashcardsets = db['flashcardsets']
bcrypt = Bcrypt(app)


# ------------------ Auth Routes ------------------
@app.route('/')
def welcome():
    return render_template('welcome.html')


@app.route('/signup', methods=['POST'])
def signup():
    username = request.form['username']
    password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')

    # Check if user exists
    if users.find_one({'username': username}):
        flash("User already exists!")
        return redirect(url_for('welcome'))

    # Create user
    result = users.insert_one({'username': username, 'password': password})

    # Auto-login
    session['username'] = username
    session['user_id'] = str(result.inserted_id)

    flash("Welcome to FlashMind!")
    return redirect(url_for('dashboard'))


@app.route('/login', methods=['POST'])
def login():
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
@app.route('/create-set', methods=['POST'])
def create_set():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    flashcardsets.insert_one({
        'user_id': ObjectId(session['user_id']),
        'name': request.form['title'],
        'created_at': datetime.utcnow()
    })
    flash("Set created!")
    return redirect(url_for('dashboard'))


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


# ------------------ Upload Notes (AJAX, Preview Step) ------------------
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

    # Generate flashcards via advanced NLP
    flashcards_generated = generate_flashcards_from_file(filepath)

    return jsonify({
        "flashcards": [
            {"question": card["question"], "answer": card["answer"], "score": card["score"]}
            for card in flashcards_generated
        ],
        "filename": filename
    })


# ------------------ Save Generated Flashcards ------------------
@app.route('/save-generated-flashcards', methods=['POST'])
def save_generated_flashcards():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = ObjectId(session['user_id'])
    questions = request.form.getlist('questions')
    answers = request.form.getlist('answers')
    set_choice = request.form.get('set_choice')
    new_set_name = request.form.get('new_set_name')

    # If user chose an existing set
    if set_choice and set_choice != "new":
        set_id = ObjectId(set_choice)
    else:
        # Create new set
        set_id = flashcardsets.insert_one({
            'user_id': user_id,
            'name': new_set_name,
            'created_at': datetime.utcnow()
        }).inserted_id

    # Insert flashcards
    for q, a in zip(questions, answers):
        flashcards.insert_one({
            'user_id': user_id,
            'set_id': set_id,
            'question': q,
            'answer': a,
            'created_at': datetime.utcnow()
        })

    flash('Flashcards saved successfully!', 'success')
    return redirect(url_for('dashboard'))


# ------------------ Review Flashcards ------------------
@app.route('/review/<set_id>')
def review_flashcards(set_id):
    flashcard_set = flashcardsets.find_one({"_id": ObjectId(set_id)})
    if not flashcard_set:
        return "Set not found", 404

    cards = list(flashcards.find({"set_id": ObjectId(set_id)}))
    for card in cards:
        for key in card:
            if isinstance(card[key], ObjectId):
                card[key] = str(card[key])

    return render_template("review_flashcards.html", flashcard_set=flashcard_set, flashcards=cards)


@app.route('/choose_review')
def choose_review():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = ObjectId(session['user_id'])
    sets = list(flashcardsets.find({'user_id': user_id}))
    return render_template('choose_review.html', sets=sets)


# ------------------ File Utility ------------------
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ------------------ Main ------------------
if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
