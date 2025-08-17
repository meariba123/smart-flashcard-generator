document.addEventListener('DOMContentLoaded', () => {
    const toggle = document.getElementById('toggle-dark');
    toggle.addEventListener('click', () => {
        document.body.classList.toggle('dark-mode');
    });
});
