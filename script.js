// Handle form submission
document.getElementById('upload-form').addEventListener('submit', async function (e) {
    e.preventDefault();

    const formData = new FormData(this);
    const resultsContainer = document.getElementById('results');
    const errorMessage = document.getElementById('error-message');

    // Clear previous results or errors
    resultsContainer.innerHTML = '';
    errorMessage.textContent = '';

    try {
        // Fetch API call to server
        const response = await fetch('/detect_emotion', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.error) {
            errorMessage.textContent = data.error;
        } else {
            resultsContainer.innerHTML = `
                <h2>Detected Emotion: ${data.emotion}</h2>
                <h3>Recommended Songs:</h3>
                <ul>
                    ${data.songs.map(song => `
                        <li>
                            <a href="${song.url}" target="_blank">${song.name} by ${song.artist}</a>
                        </li>
                    `).join('')}
                </ul>
                <h4>Submit Feedback</h4>
                <form id="feedback-form">
                    <input type="hidden" name="emotion" value="${data.emotion}">
                    <input type="hidden" name="song_name" value="${data.songs[0].name}">
                    <input type="hidden" name="song_url" value="${data.songs[0].url}">
                    <label for="feedback">Your Feedback:</label>
                    <textarea name="feedback" id="feedback" rows="3" placeholder="Enter your feedback here" required></textarea>
                    <button type="submit">Submit Feedback</button>
                </form>
            `;

            // Attach feedback listener
            attachFeedbackListener();
        }
    } catch (error) {
        errorMessage.textContent = 'An error occurred. Please try again.';
        console.error('Error:', error);
    }
});

// Handle feedback submission
function attachFeedbackListener() {
    const feedbackForm = document.getElementById('feedback-form');
    feedbackForm.addEventListener('submit', async function (e) {
        e.preventDefault();

        const formData = new FormData(this);
        const feedbackData = Object.fromEntries(formData.entries());

        try {
            const response = await fetch('/submit_feedback', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(feedbackData)
            });

            const data = await response.json();

            if (data.error) {
                alert('Error submitting feedback: ' + data.error);
            } else {
                alert('Feedback submitted successfully! Thank you!');
                feedbackForm.reset();
            }
        } catch (error) {
            alert('An error occurred while submitting feedback.');
            console.error('Error:', error);
        }
    });
}
