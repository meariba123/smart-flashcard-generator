// Dark mode toggle with localStorage to remember preference
const toggleBtn = document.getElementById('darkModeToggle');
const body = document.body;

function enableDarkMode() {
  body.classList.add('dark-mode');
  toggleBtn.textContent = '☀️';
  localStorage.setItem('flashmind-dark-mode', 'enabled');
}

function disableDarkMode() {
  body.classList.remove('dark-mode');
  toggleBtn.textContent = '🌙';
  localStorage.setItem('flashmind-dark-mode', 'disabled');
}

toggleBtn.addEventListener('click', () => {
  if (body.classList.contains('dark-mode')) {
    disableDarkMode();
  } else {
    enableDarkMode();
  }
});

// On load, check saved preference
if (localStorage.getItem('flashmind-dark-mode') === 'enabled') {
  enableDarkMode();
}

// Testimonials slider logic
const testimonials = document.querySelectorAll('.testimonial');
const prevBtn = document.querySelector('.prev-btn');
const nextBtn = document.querySelector('.next-btn');

let current = 0;

function showTestimonial(index) {
  testimonials.forEach((t, i) => {
    t.classList.toggle('active', i === index);
  });
}

// Show initial testimonial
showTestimonial(current);

prevBtn.addEventListener('click', () => {
  current = (current - 1 + testimonials.length) % testimonials.length;
  showTestimonial(current);
});
nextBtn.addEventListener('click', () => {
  current = (current + 1) % testimonials.length;
  showTestimonial(current);
});

// Auto-slide every 6 seconds
setInterval(() => {
  current = (current + 1) % testimonials.length;
  showTestimonial(current);
}, 6000);


const modalOverlay = document.getElementById("modalOverlay");
const modalContent = document.getElementById("modalInner");
const openSignupBtn = document.getElementById("openSignupBtn");
const closeModalBtn = document.getElementById("closeModalBtn");

openSignupBtn.addEventListener("click", () => {
  modalOverlay.classList.remove("hidden");
});

closeModalBtn.addEventListener("click", () => {
  modalOverlay.classList.add("hidden");
});




// Toggle between Sign Up and Log In forms
document.getElementById('showLogin').addEventListener('click', function (e) {
  e.preventDefault();
  document.getElementById('signupForm').classList.add('hidden');
  document.getElementById('loginForm').classList.remove('hidden');
});

document.getElementById('showSignup').addEventListener('click', function (e) {
  e.preventDefault();
  document.getElementById('loginForm').classList.add('hidden');
  document.getElementById('signupForm').classList.remove('hidden');
});
