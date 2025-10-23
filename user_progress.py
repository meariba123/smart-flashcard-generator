# user_progress.py
from flask import Blueprint, request, session, jsonify, current_app, render_template
from bson import ObjectId
from datetime import datetime

progress_bp = Blueprint("progress", __name__)

# ---------------- Save Quiz Result ----------------
@progress_bp.route("/save_quiz_result", methods=["POST"])
def save_quiz_result():
    db = current_app.db
    progress = db["progress"]

    if "user_id" not in session:
        return jsonify({"success": False, "error": "Not logged in"}), 403

    data = request.json
    try:
        user_id = ObjectId(session["user_id"])
        set_id = ObjectId(data["set_id"])
        score = int(data["score"])
        total = int(data["total"])
    except Exception as e:
        return jsonify({"success": False, "error": f"Invalid data: {str(e)}"}), 400

    # Find or create progress record (aggregate style)
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

    # Update aggregate stats
    record["total_attempts"] += total
    record["correct"] += score
    record["last_reviewed"] = datetime.utcnow()

    # Store individual quiz attempt
    record.setdefault("quizzes", []).append({
        "score": score,
        "total": total,
        "date": datetime.utcnow()
    })

    progress.update_one(
        {"user_id": user_id, "set_id": set_id},
        {"$set": record},
        upsert=True
    )

    return jsonify({"success": True, "message": "Quiz result saved!"})


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
