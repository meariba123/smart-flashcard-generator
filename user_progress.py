from flask import Blueprint, request, session, jsonify, render_template
from bson import ObjectId
from datetime import datetime
from app import db, flashcardsets   # import db + sets from app.py

progress_bp = Blueprint("progress", __name__)
progress = db['progress']

@progress_bp.route("/update_progress", methods=["POST"])
def update_progress():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 403

    user_id = ObjectId(session["user_id"])
    set_id = ObjectId(request.form["set_id"])
    correct = request.form["correct"] == "true"

    record = progress.find_one({"user_id": user_id, "set_id": set_id})
    if not record:
        record = {
            "user_id": user_id,
            "set_id": set_id,
            "total_attempts": 0,
            "correct": 0,
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


@progress_bp.route("/get_progress")
def get_progress():
    if "user_id" not in session:
        return jsonify([])

    user_id = ObjectId(session["user_id"])
    records = list(progress.find({"user_id": user_id}))
    data = {"sets": [], "accuracy": []}

    for rec in records:
        set_data = flashcardsets.find_one({"_id": rec["set_id"]})
        if set_data:
            acc = (rec["correct"] / rec["total_attempts"]) * 100 if rec["total_attempts"] > 0 else 0
            data["sets"].append(set_data["name"])
            data["accuracy"].append(round(acc, 2))

    return jsonify(data)


@progress_bp.route("/progress")
def progress_dashboard():
    if "user_id" not in session:
        return "Login required", 403
    return render_template("progress.html")
