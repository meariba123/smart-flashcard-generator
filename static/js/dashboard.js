document.getElementById('fileInput').onchange = function() {
    const file = this.files[0];
    if (!file) return;

    // UI Feedback: Show filename and a loading state
    document.getElementById('fileName').textContent = "Processing: " + file.name;
    
    const formData = new FormData();
    formData.append('notes_file', file);

    fetch("{{ url_for('upload_notes_ajax') }}", {
        method: "POST",
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.ok) {
            // Success! Move to the preview page
            window.location.href = data.redirect;
        } else {
            // This catches the "No text found" or "Wrong file type" errors
            alert("AI Alert: " + data.error);
        }
    })
    .catch(error => {
        console.error("Fetch Error:", error);
        alert("The server is not responding. Check your terminal for errors.");
    });
};