import re
import random

# -------------------------------
# Utility: Score flashcards
# -------------------------------
def score_flashcard(question, answer, source="general"):
    """Score flashcards so stronger ones appear first."""
    base_score = 1

    if source == "heading":
        base_score += 3
    elif source == "definition":
        base_score += 2
    elif source == "formula":
        base_score += 2
    elif source == "keyword":
        base_score += 2

    # Longer answers are usually richer
    if len(answer.split()) > 5:
        base_score += 1

    return base_score


# -------------------------------
# Core: Split into flashcards
# -------------------------------
def split_into_flashcards(text):
    """Extract flashcards from raw text using rules + regex."""

    flashcards = []
    lines = text.splitlines()

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # -------------------------------
        # 1. Heading-based Q&A
        # -------------------------------
        heading_match = re.match(r"^(#+|\d+\.|-)\s*(.+)", line)
        if heading_match:
            q = heading_match.group(2).strip()
            a = "Explain more about: " + q
            if q and a:
                flashcards.append({
                    "question": q,
                    "answer": a,
                    "score": score_flashcard(q, a, "heading")
                })
            continue

        # -------------------------------
        # 2. Definition style ("X is Y")
        # -------------------------------
        def_match = re.match(r"^(.+?)\s+(is|are|means|refers to)\s+(.+)", line, re.I)
        if def_match:
            q = f"What is {def_match.group(1).strip()}?"
            a = def_match.group(0).strip()
            if q and a:
                flashcards.append({
                    "question": q,
                    "answer": a,
                    "score": score_flashcard(q, a, "definition")
                })
            continue

        # -------------------------------
        # 3. Formula style
        # -------------------------------
        if "=" in line and any(sym in line for sym in ["+", "-", "*", "/", "^"]):
            q = "What does this formula represent?"
            a = line
            flashcards.append({
                "question": q,
                "answer": a,
                "score": score_flashcard(q, a, "formula")
            })
            continue

        # -------------------------------
        # 4. Keyword-based extraction
        # -------------------------------
        keywords = ["define", "explain", "describe", "why", "how", "advantage", "disadvantage"]
        if any(kw in line.lower() for kw in keywords):
            q = line.strip("?") + "?"
            a = "Your notes suggest this is important. Expand on: " + line
            flashcards.append({
                "question": q,
                "answer": a,
                "score": score_flashcard(q, a, "keyword")
            })
            continue

        # -------------------------------
        # 5. General sentence fallback
        # -------------------------------
        if len(line.split()) > 6 and line.endswith("."):
            q = "What does this mean?"
            a = line
            flashcards.append({
                "question": q,
                "answer": a,
                "score": score_flashcard(q, a, "general")
            })

    # Shuffle for variety, then sort by score
    random.shuffle(flashcards)
    flashcards.sort(key=lambda x: x["score"], reverse=True)

    return flashcards


# -------------------------------
# Entry: Generate flashcards
# -------------------------------
def generate_flashcards(text):
    """Main entry point for the app."""
    flashcards = split_into_flashcards(text)

    # Final clean: remove blanks
    clean_cards = [
        fc for fc in flashcards
        if fc.get("question") and fc.get("answer")
        and fc["question"].strip() and fc["answer"].strip()
    ]

    return clean_cards
