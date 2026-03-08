let queue = [...flashcards];
let currentCard = null;

function sortQueue() {
  queue.sort((a, b) => {
    const order = { red: 0, amber: 1, green: 2 };
    return order[a.status || "red"] - order[b.status || "red"];
  });
}

function getNextCard() {
  sortQueue();
  currentCard = queue[0];
  document.getElementById("masteryQuestion").textContent = currentCard.question;
}

document.getElementById("submitMastery").addEventListener("click", () => {
  const userAnswer = document.getElementById("masteryInput").value;

  fetch("/check_mastery_answer", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
      set_id: setId,
      question: currentCard.question,
      user_answer: userAnswer
    })
  })
  .then(res => res.json())
  .then(data => {
    document.getElementById("masteryFeedback").textContent =
      data.correct ? "✅ Correct" : "❌ Incorrect";

    currentCard.status = data.status;
    currentCard.mastery_score = data.mastery_score;

    updateStats();
    getNextCard();
  });
});

function updateStats() {
  const green = queue.filter(c => c.status === "green").length;
  const amber = queue.filter(c => c.status === "amber").length;
  const red = queue.filter(c => c.status === "red").length;

  document.getElementById("masteryStats").textContent =
    `Green: ${green} | Amber: ${amber} | Red: ${red}`;
}

getNextCard();
updateStats();