document.getElementById('fileInput').onchange = function() {
    const file = this.files[0];
    if (!file) return;

    const uploadForm = document.getElementById('uploadForm');
    const loadingStatus = document.getElementById('loadingStatus');
    const progressText = document.getElementById('progressPercent');
    const ring = document.querySelector('.progress-ring__circle');
    const circumference = 52 * 2 * Math.PI;

    // Setup Ring
    ring.style.strokeDasharray = `${circumference} ${circumference}`;
    ring.style.strokeDashoffset = circumference;

    function setProgress(percent) {
        const offset = circumference - (percent / 100 * circumference);
        ring.style.strokeDashoffset = offset;
        progressText.innerText = `${percent}%`;
    }

    uploadForm.style.display = 'none';
    loadingStatus.style.display = 'block';

    let width = 0;
    const interval = setInterval(() => {
        if (width >= 96) {
            clearInterval(interval);
        } else {
            width += Math.floor(Math.random() * 8) + 1;
            setProgress(width);
        }
    }, 500);

    const formData = new FormData();
    formData.append('notes_file', file);
    formData.append('target_lang', document.getElementById('targetLanguage').value);

    fetch(UPLOAD_URL, { method: "POST", body: formData })
    .then(res => res.json())
    .then(data => {
        clearInterval(interval);
        setProgress(100);
        if (data.ok) window.location.href = data.redirect;
        else {
            alert(data.error);
            uploadForm.style.display = 'block';
            loadingStatus.style.display = 'none';
        }
    });
};