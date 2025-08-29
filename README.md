# FlashMind: Our Smart Flashcard Generator 

An AI-powered web application that helps students generate, save, and review flashcards automatically from lecture notes.

## Features
- **User Authentication** – Register/Login with secure password hashing.
- **Flashcard Generation** – Upload lecture notes (`.txt`, `.docx`, `.pdf`) and automatically generate flashcards using NLP.
- **Confidence Scoring** – Each flashcard includes a confidence level (green = strong match, red = weaker).
- **Flashcard Sets** – Organize flashcards into named sets stored in MongoDB.
- **Interactive Review** – Flip cards, shuffle, and track progress with a progress bar.
- **Quiz Mode** – Test yourself on the flashcards, get instant feedback, and track your score.
- **Dark Mode & Animations** – Modern, student-friendly design with toggleable dark mode.
- **MongoDB Integration** – All users, flashcards, and sets are securely stored in a NoSQL database.

## Tech Stack
- **Backend:** Python, Flask
- **Database:** MongoDB
- **Frontend:** HTML, CSS, JavaScript (with animations)
- **NLP:** Python (custom heuristics + scoring system for Q&A extraction)

## 📂 Project Structure
smart-flashcard-generator/
│
├── app.py # Flask backend
├── templates/ # HTML templates
├── static/ # CSS, JS, images
├── uploads/ # Uploaded lecture files
└── .env # MongoDB URI & secret key

## ⚙️ Setup Instructions
1. Clone this repository:
   ```bash
   git clone https://github.com/your-username/smart-flashcard-generator.git
   cd smart-flashcard-generator

2. Install Dependencies:
   pip install -r requirements.txt

3. Create an .env file with:
   MONGO_URI=mongodb://localhost:27017/flashcarddb
   SECRET_KEY=supersecretkey

4. Run Flask App:
   python app.py

5. Open in browser:
   http://localhost:5000

