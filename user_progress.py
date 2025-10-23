# user_progress.py
from flask import Blueprint, request, session, jsonify, current_app, render_template
from bson import ObjectId
from datetime import datetime

progress_bp = Blueprint("progress", __name__)

# ---------------- Save Quiz Result ----------------
@user_progress.route("/save_quiz_result", methods=["POST"])
def save_quiz_result():
    try:
        # Get current user
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "Not logged in"}), 401

        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        set_id = data.get("set_id")
        score = data.get("score")
        total = data.get("total")

        # Validate all fields
        if not set_id or score is None or total is None:
            return jsonify({"error": "Missing required fields"}), 400

        # Convert to ObjectId safely
        try:
            set_obj_id = ObjectId(set_id)
        except Exception:
            return jsonify({"error": "Invalid set_id"}), 400

        # Get the flashcard set
        flashcard_set = mongo.flashcards.find_one({"_id": set_obj_id, "user_id": user_id})
        if not flashcard_set:
            return jsonify({"error": "Set not found or not owned by user"}), 404

        # Create progress record
        progress_data = {
            "user_id": user_id,
            "set_id": set_obj_id,
            "score": score,
            "total": total,
            "timestamp": datetime.utcnow()
        }

        # Save to user_progress collection
        mongo.user_progress.insert_one(progress_data)

        # Optionally: Update the flashcard set with last quiz info
        mongo.flashcards.update_one(
            {"_id": set_obj_id},
            {"$set": {"last_quiz_score": score, "last_quiz_total": total, "last_quiz_date": datetime.utcnow()}}
        )

        return jsonify({"message": "Quiz result saved successfully"}), 200

    except Exception as e:
        print("Error saving quiz result:", e)
        return jsonify({"error": "Server error"}), 500

# ---------------- Update Progress (per card) ----------------
@progress_bp.route("/update_progress", methods=["POST"])
def update_progress():
    db = current_app.db
    progress = db["progress"]

    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 403

    try:
        user_id = ObjectId(session["user_id"])
        set_id = ObjectId(request.form["set_id"])
    except Exception as e:
        return jsonify({"error": f"Invalid ids: {str(e)}"}), 400

    correct = request.form.get("correct", "false") == "true"

    record = progress.find_one({"user_id": user_id, "set_id": set_id})
    if not record:
        record = {
            "user_id": user_id,
            "set_id": set_id,
            "total_attempts": 0,
            "correct": 0,
            "quizzes": [],
            "last_reviewed": datetime.utcnow()
        }

    record["total_attempts"] += 1
    if correct:
        record["correct"] += 1
    record["last_reviewed"] = datetime.utcnow()

    progress.update_one(
        {"user_id": user_id, "set_id": set_id},
        {"$set": record},
        upsert=True
    )

    return jsonify({"ok": True})


# ---------------- Progress Page (renders dashboard) ----------------
@progress_bp.route("/progress")
def progress_page():
    return render_template("progress.html")


# ---------------- Get Progress (JSON API for charts) ----------------
@progress_bp.route("/get_progress")
def get_progress():
    db = current_app.db
    progress = db["progress"]
    flashcardsets = db["flashcardsets"]

    if "user_id" not in session:
        return jsonify({"sets": [], "accuracy": []})

    user_id = ObjectId(session["user_id"])
    records = list(progress.find({"user_id": user_id}))
    data = {"sets": [], "accuracy": []}

    for rec in records:
        # rec["set_id"] is an ObjectId in DB - safe to use
        set_data = flashcardsets.find_one({"_id": rec["set_id"]})
        if set_data:
            acc = (rec["correct"] / rec["total_attempts"]) * 100 if rec["total_attempts"] > 0 else 0
            data["sets"].append(set_data.get("name", "Unnamed Set"))
            data["accuracy"].append(round(acc, 2))

    return jsonify(data)
