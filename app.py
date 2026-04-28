from bson import ObjectId
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, current_app
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
from werkzeug.utils import secure_filename
from datetime import datetime
import os

#Import advanced NLP pipeline (keep your existing nlp.py)
from nlp import extract_text_from_file, generate_flashcards_from_file, is_answer_correct

#Import blueprint that contains progress routes
from user_progress import progress_bp

# Environment + Flask Setup
load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback_secret')
app.config['UPLOAD_FOLDER'] = 'uploads'
ALLOWED_EXTENSIONS = {'txt','doc','docx','pdf','ppt','pptx','png','jpg','jpeg'}
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

#MongoDB Setup
client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"))
db = client['flashcarddb']   
users = db['users']
flashcards = db['flashcards']
flashcardsets = db['flashcardsets']
progress = db['progress']

#Expose db for blueprints to use current_app.db
app.db = db

bcrypt = Bcrypt(app)

# Register blueprint (no prefix so endpoints are global, matching existing frontend)
app.register_blueprint(progress_bp)


#Auth Routes 
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


# Dashboard 
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    sets = list(flashcardsets.find({'user_id': ObjectId(session['user_id'])}))
    return render_template('dashboard.html', sets=sets)


#  Create Flashcard Set 
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


#  Create Flashcard Manually 
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


#  View Flashcard Set 
@app.route('/set/<set_id>')
def view_set(set_id):

    cards = list(flashcards.find({'set_id': ObjectId(set_id)}))
    set_data = flashcardsets.find_one({'_id': ObjectId(set_id)})

    set_data['_id'] = str(set_data['_id'])

    for c in cards:
        c['_id'] = str(c['_id'])

    return render_template('view_set.html',
                           set_data=set_data,
                           flashcards=cards)


#Upload Notes (AJAX) 
@app.route('/upload_notes_ajax', methods=['POST'])
def upload_notes_ajax():
    try:
        if 'notes_file' not in request.files:
            return jsonify({"ok": False, "error": "No file uploaded"}), 400

        file = request.files['notes_file']
        
   
        target_lang = request.form.get('target_lang', 'en') 

        if file.filename == '':
            return jsonify({"ok": False, "error": "No file selected"}), 400

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

          
            flashcards_generated = generate_flashcards_from_file(filepath, language=target_lang)

            if not flashcards_generated:
                return jsonify({"ok": False, "error": "AI could not find enough text."}), 200

            # Store in session, including the language used
            session['temp_generated'] = [
                {
                    "question": c.get("question",""), 
                    "answer": c.get("answer",""), 
                    "score": c.get("score", 0),
                    "visual_explanation": c.get("visual_explanation"),
                    "image_url": c.get("image_url"),
                    "language": target_lang  # NEW: keep track of the language
                }
                for c in flashcards_generated
            ]
            session['temp_filename'] = filename

            return jsonify({"ok": True, "redirect": url_for('review_temp')})
        
        return jsonify({"ok": False, "error": "File type not allowed"}), 400

    except Exception as e:
        print(f"Server Error: {str(e)}")
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route('/review-temp')
def review_temp():
    temp = session.get('temp_generated')
    if not temp:
        flash('No generated flashcards to review yet.', 'warning')
        return redirect(url_for('dashboard'))

    flashcard_set = {"name": "Unsaved Generated Set"}
    return render_template(
        'study_flashcards.html',
        flashcard_set=flashcard_set,
        flashcards=temp,
        temp_mode=True
    )

@app.route('/view_sets')
def view_sets():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = ObjectId(session['user_id'])
    sets = list(flashcardsets.find({'user_id': user_id}))

    for s in sets:

        # convert ObjectId once
        set_object_id = s['_id']
        s['_id'] = str(set_object_id)

        cards = list(flashcards.find({'set_id': set_object_id}))
        s['count'] = len(cards)

        prog = list(progress.find({'set_id': set_object_id}))

        if prog:
            avg = sum(p.get('score', 0) for p in prog) / len(prog)
            s['avg_score'] = avg
        else:
            s['avg_score'] = 0

    return render_template('view_sets.html', sets=sets)


#Preview Generated Flashcards 
@app.route('/preview-generated/<filename>')
def preview_generated_flashcards(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    generated = generate_flashcards_from_file(filepath)
    return render_template('preview_generated.html', flashcards=generated)


# Save Generated Flashcards 
@app.route('/save-generated-flashcards', methods=['POST'])
def save_generated_flashcards():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = ObjectId(session['user_id'])
    set_name = request.form.get('set_name')
    temp_cards = session.get('temp_generated', [])
    
    set_lang = temp_cards[0].get('language', 'en') if temp_cards else 'en'

    timestamp = datetime.utcnow().strftime("%H:%M")
    display_name = f"{set_name} ({timestamp})" if set_name else f"New Set ({timestamp})"

    set_id = flashcardsets.insert_one({
        'user_id': user_id,
        'name': display_name, # Using the unique name
        'language': set_lang, 
        'created_at': datetime.utcnow()
    }).inserted_id

    # 2. Save the individual cards
    for card in temp_cards:
        flashcards.insert_one({ 
            'user_id': user_id,
            'set_id': set_id,
            'question': card.get('question'),
            'answer': card.get('answer'),
            'language': card.get('language', set_lang), 
            'visual_explanation': card.get('visual_explanation'),
            'score': card.get('score', 0),
            'status': 'red',
            'attempts': 0,
            'correct_attempts': 0,
            'created_at': datetime.utcnow()
        })

    session.pop('temp_generated', None)
    session.pop('temp_filename', None)

    # 3. Now set_lang is guaranteed to exist
    flash(f'Set saved successfully! Starting your quiz...', 'success')
    
    return redirect(url_for('quiz_flashcards', set_id=str(set_id)))

@app.route("/study/<set_id>")
def study_flashcards(set_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = ObjectId(session["user_id"])
    flashcard_set = flashcardsets.find_one({"_id": ObjectId(set_id), "user_id": user_id})
    
    if not flashcard_set:
        return "Set not found", 404

    cards = list(flashcards.find({"set_id": ObjectId(set_id), "user_id": user_id}))
    
    # Convert the set ID
    flashcard_set["_id"] = str(flashcard_set["_id"])
    
    for card in cards:
        card["_id"] = str(card["_id"])
        if "set_id" in card:
            card["set_id"] = str(card["set_id"])
        if "user_id" in card:
            card["user_id"] = str(card["user_id"])

    total_cards = len(cards)
    mastered_count = sum(1 for c in cards if c.get('status') == 'green' or c.get('mastery_score', 0) >= 0.8)
    percent = int((mastered_count / total_cards) * 100) if total_cards > 0 else 0

    return render_template(
        "study_flashcards.html",
        flashcard_set=flashcard_set,
        flashcards=cards,
        set_id=set_id,
        mastery_percent=percent,
        temp_mode=False
    )

#  Quiz Mode 
@app.route("/quiz/<set_id>")
def quiz_flashcards(set_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = ObjectId(session["user_id"])
    flashcard_set = flashcardsets.find_one({"_id": ObjectId(set_id), "user_id": user_id})

    if not flashcard_set:
        return "Set not found", 404

    # Fetch the cards
    cards = list(flashcards.find({"set_id": ObjectId(set_id), "user_id": user_id}))
    
    # Progress calculations
    total = len(cards)
    mastered = sum(1 for c in cards if c.get('status') == 'green')
    percent = int((mastered / total) * 100) if total > 0 else 0

    #Convert ObjectIds to Strings 
    flashcard_set["_id"] = str(flashcard_set["_id"])
    for card in cards:
        card["_id"] = str(card["_id"])
        # If set_id is also in the card object, convert it too
        if "set_id" in card:
            card["set_id"] = str(card["set_id"])
        if "user_id" in card:
            card["user_id"] = str(card["user_id"])

    return render_template(
        "quiz_flashcards.html",
        flashcard_set=flashcard_set,
        flashcards=cards, # This is now safe for |tojson
        set_id=str(set_id),
        mastery_percent=percent
    )

 
# Mastery Mode 
@app.route("/mastery/<set_id>")
def mastery_mode(set_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = ObjectId(session["user_id"])
    flashcard_set = flashcardsets.find_one({"_id": ObjectId(set_id), "user_id": user_id})

    if not flashcard_set:
        return "Set not found", 404

    # Convert the set's own ID to string
    flashcard_set["_id"] = str(flashcard_set["_id"])

    # Fetch and CLEAN the cards explicitly
    raw_cards = list(flashcards.find({"set_id": ObjectId(set_id), "user_id": user_id}))
    
    clean_cards = []
    for card in raw_cards:
        clean_cards.append({
            "_id": str(card["_id"]),
            "set_id": str(card["set_id"]),
            "question": card.get("question", ""),
            "answer": card.get("answer", ""),
            "status": card.get("status", "red"),
            "mastery_score": card.get("mastery_score", 0),
            "attempts": card.get("attempts", 0),
            "xp": card.get("xp", 0),
            "current_streak": card.get("current_streak", 0),
            "visual_explanation": card.get("visual_explanation", "")
        })

    return render_template(
        "mastery_mode.html",
        flashcards=clean_cards,  # Pass the cleaned list
        set_id=str(set_id),
        flashcard_set=flashcard_set
    )

#  Basic Quiz Answer Check 
@app.route("/check_answer", methods=["POST"])
def check_answer():
    data = request.get_json()
    user_answer = data.get("user_answer", "")
    correct_answer = data.get("correct_answer", "")

    if is_answer_correct(user_answer, correct_answer):
        return jsonify({"correct": True})
    else:
        return jsonify({"correct": False, "correct_answer": correct_answer})
    

#  Mastery Answer Check 
@app.route("/check_mastery_answer", methods=["POST"])
def check_mastery_answer():
    data = request.json
    card_id = data["card_id"]
    user_answer = data["user_answer"]

    card = flashcards.find_one({"_id": ObjectId(card_id)})
    if not card:
        return jsonify({"error": "Card not found"}), 404

    # Get current stats or default to 0
    attempts = card.get("attempts", 0) + 1
    correct_attempts = card.get("correct_attempts", 0)
    streak = card.get("current_streak", 0)
    xp = card.get("xp", 0)

    is_correct = is_answer_correct(user_answer, card["answer"])

    if is_correct:
        correct_attempts += 1
        streak += 1
        xp += 10
    else:
        streak = 0

    # Calculate Accuracy
    accuracy = correct_attempts / attempts
    # Use the AI generation score as a baseline for difficulty/confidence
    ai_conf = card.get("score", 0.7)

    # Mastery Calculation: 40% AI confidence, 60% user accuracy
    mastery = round((0.4 * ai_conf) + (0.6 * accuracy), 2)


    if mastery >= 0.8:
        status = "green"
    elif mastery >= 0.5:
        status = "amber"
    else:
        status = "red"

    flashcards.update_one(
        {"_id": ObjectId(card_id)},
        {"$set": {
            "attempts": attempts,
            "correct_attempts": correct_attempts,
            "mastery_score": mastery,
            "status": status,
            "current_streak": streak,
            "xp": xp
        }}
    )

    return jsonify({
        "correct": is_correct,
        "status": status,
        "mastery_score": mastery,
        "streak": streak,
        "xp": xp
    })

@app.route("/set/<set_id>/mastery-analytics")
def set_mastery_analytics(set_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = ObjectId(session["user_id"])
    set_data = flashcardsets.find_one({"_id": ObjectId(set_id), "user_id": user_id})
    cards = list(flashcards.find({"set_id": ObjectId(set_id)}))

    # Stats for the sidebar
    total = len(cards)
    green = sum(1 for c in cards if c.get('status') == 'green')
    amber = sum(1 for c in cards if c.get('status') == 'amber')
    red = sum(1 for c in cards if c.get('status') == 'red' or not c.get('status'))
    
    mastery_percent = int((green / total) * 100) if total > 0 else 0

    # Clean cards for the UI
    for c in cards:
        c['_id'] = str(c['_id'])
        c['status'] = c.get('status', 'red')
        c['mastery_score'] = c.get('mastery_score', 0)

    return render_template(
        "view_mastery.html",
        set_data=set_data,
        cards=cards,
        stats={'total': total, 'green': green, 'amber': amber, 'red': red, 'percent': mastery_percent}
    )

@app.route("/edit_flashcard", methods=["POST"])
def edit_flashcard():
    if "user_id" not in session:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    
    data = request.json
    card_id = data.get("card_id")
    new_question = data.get("question")
    new_answer = data.get("answer")

    if not card_id or not new_question or not new_answer:
        return jsonify({"success": False, "error": "Missing data"}), 400

    result = db.flashcards.update_one(
        {"_id": ObjectId(card_id), "user_id": ObjectId(session["user_id"])},
        {"$set": {"question": new_question, "answer": new_answer}}
    )

    if result.modified_count > 0:
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Update failed or no changes made"})

#  File Utility 
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Main 
if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)

