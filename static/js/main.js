// main.js

document.addEventListener("DOMContentLoaded", () => {
    // Preloader
    const preloader = document.getElementById('preloader');
    window.addEventListener("load", () => {
        preloader.style.opacity = 0;
        preloader.style.pointerEvents = 'none';
        setTimeout(() => preloader.style.display = 'none', 500);
    });

    // Smooth scroll
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener("click", function(e) {
            e.preventDefault();
            document.querySelector(this.getAttribute("href")).scrollIntoView({
                behavior: "smooth"
            });
        });
    });

    // Scroll animation for steps
    const steps = document.querySelectorAll('.step.animate');
    const observer = new IntersectionObserver(entries => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.3 });

    steps.forEach(step => {
        observer.observe(step);
    });

    // Hamburger menu
    const menuToggle = document.querySelector('.menu-toggle');
    const navLinks = document.querySelector('.nav-links');
    menuToggle.addEventListener('click', () => {
        navLinks.classList.toggle('active');
    });

    // Dark mode
    const toggleDark = document.getElementById("toggle-dark");
    const body = document.body;

    toggleDark.addEventListener("click", () => {
        body.classList.toggle("dark-mode");

        if (body.classList.contains("dark-mode")) {
            toggleDark.textContent = "☀️";
        } else {
            toggleDark.textContent = "🌙";
        }
    });

    // Video Carousel
    const carousel = document.querySelector('.carousel-track');
    const prev = document.querySelector('.carousel-button.prev');
    const next = document.querySelector('.carousel-button.next');

    if (carousel && prev && next) {
        const slides = Array.from(carousel.children);
        let index = 0;

        function showSlide(i) {
            carousel.style.transform = `translateX(-${i * 100}%)`;
        }

        next.addEventListener('click', () => {
            index = (index + 1) % slides.length;
            showSlide(index);
        });

        prev.addEventListener('click', () => {
            index = (index - 1 + slides.length) % slides.length;
            showSlide(index);
        });
    }
});
