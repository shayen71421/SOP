let currentLanguage = 'english';
const API_URL = 'https://upgraded-cod-7wqvw5497j6frgwr.github.dev/api';

function changeLanguage(lang) {
    currentLanguage = lang;
    addMessage(`Language changed to ${lang}`, 'bot');
}

function addMessage(text, sender) {
    const container = document.getElementById('chat-container');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    messageDiv.textContent = text;
    container.appendChild(messageDiv);
    container.scrollTop = container.scrollHeight;
}

async function sendMessage() {
    const input = document.getElementById('user-input');
    const message = input.value.trim();
    if (!message) return;

    addMessage(message, 'user');
    input.value = '';

    try {
        const response = await fetch(`${API_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                language: currentLanguage
            })
        });
        const data = await response.json();
        addMessage(data.response, 'bot');
    } catch (error) {
        addMessage('Error: Could not reach the server', 'bot');
    }
}