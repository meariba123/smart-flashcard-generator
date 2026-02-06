function handleFileUpload() {
    const fileInput = document.getElementById('fileInput');
    const status = document.getElementById('loadingStatus');
    const file = fileInput.files[0];

    if (!file) return;

    // Show the file name and loading state
    document.getElementById('fileName').textContent = file.name;
    status.style.display = 'block';

    // Create the data package to send to Python
    const formData = new FormData();
    formData.append('notes_file', file);

    // Send to your /upload_notes_ajax route
    fetch("{{ url_for('upload_notes_ajax') }}", {
        method: "POST",
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.ok) {
            // Redirect to the review page as defined in your app.py
            window.location.href = data.redirect;
        } else {
            alert("Upload failed: " + (data.error || "Unknown error"));
            status.style.display = 'none';
        }
    })
    .catch(error => {
        console.error("Error:", error);
        alert("An error occurred during upload.");
        status.style.display = 'none';
    });
}