// mastery_mode.js

let allCards = [...flashcards]; 
let currentCard = null;

/**
 * Grabs the next card that isn't 'green'.
 * If all are green, shows the success screen.
 */
function getNextCard() {
    // 1. Filter out already mastered cards
    const remaining = allCards.filter(c => c.status !== "green");

    // 2. If nothing is left, stop the loop
    if (remaining.length === 0) {
        document.getElementById("masteryCard").style.display = "none";
        document.getElementById("masteryComplete").style.display = "block";
        document.getElementById("masteryStats").innerHTML = "<b>Session Complete! 100% Mastered</b>";
        return;
    }

    // 3. Sort remaining: Red first, then Amber
    remaining.sort((a, b) => {
        const order = { red: 0, amber: 1 };
        const statusA = a.status || "red";
        const statusB = b.status || "red";
        return order[statusA] - order[statusB];
    });

    // 4. Set current card and update UI
    currentCard = remaining[0];
    document.getElementById("masteryQuestion").textContent = currentCard.question;
    document.getElementById("masteryInput").value = "";
    document.getElementById("masteryFeedback").textContent = "";
}

document.getElementById("submitMastery").addEventListener("click", () => {
    const userAnswer = document.getElementById("masteryInput").value;
    const btn = document.getElementById("submitMastery");

    if (!userAnswer.trim()) {
        alert("Please enter an answer.");
        return;
    }

    btn.disabled = true;
    btn.innerText = "Checking...";

    fetch("/check_mastery_answer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            card_id: currentCard._id,
            user_answer: userAnswer
        })
    })
    .then(res => res.json())
    .then(data => {
        // Show feedback
        const feedback = document.getElementById("masteryFeedback");
        feedback.innerHTML = data.correct ? "✅ Spot on!" : `❌ Not quite. (Status: ${data.status})`;
        feedback.className = data.correct ? "feedback-msg correct" : "feedback-msg incorrect";

        // Update the local data so the filter picks it up next time
        const index = allCards.findIndex(c => c._id === currentCard._id);
        if (index !== -1) {
            allCards[index].status = data.status;
            allCards[index].mastery_score = data.mastery_score;
        }

        updateStats();

        // Brief delay for the user to read feedback, then next card
        setTimeout(() => {
            btn.disabled = false;
            btn.innerText = "Submit Answer";
            getNextCard();
        }, 1500);
    })
    .catch(err => {
        console.error("Error:", err);
        btn.disabled = false;
        btn.innerText = "Error - Try Again";
    });
});

function updateStats() {
    const green = allCards.filter(c => c.status === "green").length;
    const amber = allCards.filter(c => c.status === "amber").length;
    const red = allCards.filter(c => (!c.status || c.status === "red")).length;

    document.getElementById("masteryStats").innerHTML = `
        <span style="color:#2ecc71">● Green: ${green}</span> | 
        <span style="color:#f39c12">● Amber: ${amber}</span> | 
        <span style="color:#e74c3c">● Red: ${red}</span>
    `;
}

// Start the session
updateStats();
getNextCard();