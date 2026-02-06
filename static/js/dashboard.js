// dashboard.js

document.getElementById('fileInput').onchange = function() {
    const file = this.files[0];
    const fileNameDisplay = document.getElementById('fileName');
    
    if (!file) return;

    // 1. UI Feedback: Show filename and a loading state
    fileNameDisplay.textContent = "Processing: " + file.name;
    fileNameDisplay.style.color = "#5d2a9d"; // Matching your purple theme
    
    const formData = new FormData();
    formData.append('notes_file', file);

    // 2. The Fetch Request
    // We use the UPLOAD_URL variable defined in the HTML file
    fetch(UPLOAD_URL, {
        method: "POST",
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            // This catches 404 or 500 errors from the server
            throw new Error('Server error: ' + response.status);
        }
        return response.json();
    })
    .then(data => {
        if (data.ok) {
            // Success! Move to the preview page
            window.location.href = data.redirect;
        } else {
            // Handles AI errors like "No text found"
            alert("AI Alert: " + data.error);
            fileNameDisplay.textContent = "Upload failed. Try again.";
            fileNameDisplay.style.color = "red";
        }
    })
    .catch(error => {
        console.error("Fetch Error:", error);
        // This triggers if the server is off or the URL is wrong
        alert("The server is not responding. Check your terminal for errors.");
    });
};