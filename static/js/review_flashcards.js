// review_flashcards.js
let flashcards = [...flashcardsData];
let currentIndex = 0;
let flipped = false;

const flashcardEl = document.getElementById('flashcard');
const questionEl = document.getElementById('cardQuestion');
const answerEl = document.getElementById('cardAnswer');
const progressEl = document.getElementById('progress');
const cardCounterEl = document.getElementById('cardCounter');

const prevBtn = document.getElementById('prevBtn');
const nextBtn = document.getElementById('nextBtn');
const shuffleBtn = document.getElementById('shuffleBtn');
const startQuizBtn = document.getElementById('startQuizBtn');
const downloadBtn = document.getElementById('downloadBtn');

const quizModal = document.getElementById('quizModal');
const quizQuestion = document.getElementById('quizQuestion');
const quizAnswerInput = document.getElementById('quizAnswerInput');
const quizFeedback = document.getElementById('quizFeedback');
const submitAnswerBtn = document.getElementById('submitAnswerBtn');
const closeQuizBtn = document.getElementById('closeQuizBtn');
const quizProgress = document.getElementById('quizProgress');

const darkToggle = document.getElementById('darkModeToggle');

let quizIndex = 0;
let quizScore = 0;

// ---------------- Card Functions ----------------
function showCard(index) {
  flipped = false;
  flashcardEl.classList.remove('flipped');
  questionEl.textContent = flashcards[index].question;
  answerEl.textContent = flashcards[index].answer;
  progressEl.max = flashcards.length;
  progressEl.value = index + 1;
  cardCounterEl.textContent = `${index + 1} / ${flashcards.length}`;
}

function flipCard() {
  flipped = !flipped;
  flashcardEl.classList.toggle('flipped', flipped);
}

function nextCard() {
  if (currentIndex < flashcards.length - 1) {
    currentIndex++;
    showCard(currentIndex);
  }
}

function prevCard() {
  if (currentIndex > 0) {
    currentIndex--;
    showCard(currentIndex);
  }
}

function shuffleCards() {
  for (let i = flashcards.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [flashcards[i], flashcards[j]] = [flashcards[j], flashcards[i]];
  }
  currentIndex = 0;
  showCard(currentIndex);
}

// ---------------- Download CSV ----------------
function downloadFlashcardsCSV() {
  const csvRows = ['Question,Answer'];
  flashcards.forEach(fc => {
    let q = fc.question.replace(/"/g, '""');
    let a = fc.answer.replace(/"/g, '""');
    csvRows.push(`"${q}","${a}"`);
  });
  const blob = new Blob([csvRows.join('\n')], {type: 'text/csv'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'flashcards.csv';
  document.body.appendChild(a);
  a.click();
  a.remove();
}

// ---------------- Quiz Functions ----------------
function startQuiz() {
  quizIndex = 0;
  quizScore = 0;
  quizModal.classList.remove('hidden');
  showQuizQuestion(quizIndex);
  updateQuizProgress();
  quizAnswerInput.focus();
}

function finishQuiz(score, total){
  fetch("/save_quiz_result", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      set_id: "{{ flashcard_set._id }}",
      score: score,
      total: total
    })
  })
  .then(res => res.json())
  .then(data => {
    console.log("Quiz saved:", data);
  });
}


function showQuizQuestion(index) {
  quizAnswerInput.value = '';
  quizFeedback.textContent = '';
  quizQuestion.textContent = flashcards[index].question;
}

function submitQuizAnswer() {
  const userAnswer = quizAnswerInput.value.trim().toLowerCase();
  const correctAnswer = flashcards[quizIndex].answer.trim().toLowerCase();
  if (userAnswer === correctAnswer) {
    quizScore++;
    quizFeedback.textContent = "✅ Correct!";
    quizFeedback.style.color = "green";
  } else {
    quizFeedback.textContent = `❌ Correct answer: ${flashcards[quizIndex].answer}`;
    quizFeedback.style.color = "red";
  }
  setTimeout(() => {
    quizIndex++;
    if (quizIndex < flashcards.length) {
      showQuizQuestion(quizIndex);
      updateQuizProgress();
    } else {
      quizFeedback.textContent = `🎉 Quiz complete! Score: ${quizScore}/${flashcards.length}`;
      quizAnswerInput.style.display = 'none';
      submitAnswerBtn.style.display = 'none';
      launchConfetti();
    }
  }, 1500);
}

function updateQuizProgress() {
  quizProgress.textContent = `Question ${quizIndex + 1} of ${flashcards.length}`;
}

function closeQuiz() {
  quizModal.classList.add('hidden');
  quizAnswerInput.style.display = 'block';
  submitAnswerBtn.style.display = 'inline-block';
}

function endQuiz(score, total) {
  fetch("/save_quiz_result", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      set_id: "{{ flashcard_set._id }}", // Jinja injects the set id
      score: score,
      total: total
    })
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      alert(`Quiz saved! You scored ${score}/${total}`);
    } else {
      alert("Error saving quiz: " + (data.error || "unknown"));
    }
  });
}


// ---------------- Dark Mode ----------------
darkToggle.addEventListener('click', () => {
  document.body.classList.toggle('dark-mode');
  localStorage.setItem('flashmindDarkMode', document.body.classList.contains('dark-mode'));
});
if (localStorage.getItem('flashmindDarkMode') === 'true') {
  document.body.classList.add('dark-mode');
}

// ---------------- Swipe Gestures ----------------
let touchStartX = 0;
flashcardEl.addEventListener('touchstart', e => touchStartX = e.touches[0].clientX);
flashcardEl.addEventListener('touchend', e => {
  let touchEndX = e.changedTouches[0].clientX;
  if (touchEndX - touchStartX > 50) prevCard();
  else if (touchStartX - touchEndX > 50) nextCard();
  else flipCard();
});

// ---------------- Keyboard Shortcuts ----------------
document.addEventListener('keydown', e => {
  if (e.key === 'ArrowRight') nextCard();
  if (e.key === 'ArrowLeft') prevCard();
  if (e.key === ' ' || e.key === 'Spacebar') {
    e.preventDefault();
    flipCard();
  }
});

// ---------------- Confetti ----------------
function launchConfetti() {
  const canvas = document.getElementById('confettiCanvas');
  const ctx = canvas.getContext('2d');
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;

  let particles = [];
  for (let i = 0; i < 150; i++) {
    particles.push({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height - canvas.height,
      r: Math.random() * 6 + 2,
      d: Math.random() * 0.5 + 0.5,
      color: `hsl(${Math.random()*360},100%,50%)`,
      tilt: Math.random() * 10 - 10
    });
  }

  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    particles.forEach(p => {
      ctx.beginPath();
      ctx.fillStyle = p.color;
      ctx.arc(p.x, p.y, p.r, 0, Math.PI*2, false);
      ctx.fill();
    });
    update();
  }

  function update() {
    particles.forEach(p => {
      p.y += p.d;
      p.x += Math.sin(p.tilt);
      if (p.y > canvas.height) p.y = -10;
    });
  }

  let duration = 3000;
  let start = null;
  function animate(timestamp) {
    if (!start) start = timestamp;
    let progress = timestamp - start;
    draw();
    if (progress < duration) requestAnimationFrame(animate);
    else ctx.clearRect(0, 0, canvas.width, canvas.height);
  }
  animate();
}

// ---------------- Event Listeners ----------------
flashcardEl.addEventListener('click', flipCard);
prevBtn.addEventListener('click', prevCard);
nextBtn.addEventListener('click', nextCard);
shuffleBtn.addEventListener('click', shuffleCards);
startQuizBtn.addEventListener('click', startQuiz);
submitAnswerBtn.addEventListener('click', submitQuizAnswer);
closeQuizBtn.addEventListener('click', closeQuiz);
downloadBtn.addEventListener('click', downloadFlashcardsCSV);

// Init
showCard(currentIndex);


