document.addEventListener('DOMContentLoaded', () => {
    const chatBox = document.getElementById('chat-box');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');

    fetchHistory();

    function addMessageToUI(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', role);
        messageDiv.textContent = content;
        chatBox.appendChild(messageDiv);
        scrollToBottom();
    }

    function scrollToBottom() {
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function addLoadingIndicator() {
        const loadingDiv = document.createElement('div');
        loadingDiv.classList.add('message', 'assistant', 'loading');
        loadingDiv.id = 'loading-indicator';
        loadingDiv.textContent = 'Thinking...';
        chatBox.appendChild(loadingDiv);
        scrollToBottom();
    }

    function removeLoadingIndicator() {
        const loadingDiv = document.getElementById('loading-indicator');
        if (loadingDiv) {
            loadingDiv.remove();
        }
    }

    async function fetchHistory() {
        try {
            const response = await fetch('/history');
            const messages = await response.json();
            
            messages.forEach(msg => {
                addMessageToUI(msg.role, msg.content);
            });
            
            if (messages.length === 0) {
                const welcomeDiv = document.createElement('div');
                welcomeDiv.style.textAlign = 'center';
                welcomeDiv.style.color = '#888';
                welcomeDiv.style.marginTop = '20px';
                welcomeDiv.textContent = "Say hello to awaken the AI...";
                chatBox.appendChild(welcomeDiv);
            }
        } catch (error) {
            console.error('Error fetching history:', error);
        }
    }

    async function sendMessage() {
        const text = userInput.value.trim();
        if (!text) return;

        if (chatBox.children.length === 1 && chatBox.children[0].textContent.includes("awaken the AI")) {
            chatBox.innerHTML = '';
        }

        userInput.value = '';
        userInput.disabled = true;
        sendBtn.disabled = true;

        addMessageToUI('user', text);
        addLoadingIndicator();

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: text })
            });

            removeLoadingIndicator();

            if (response.ok) {
                const data = await response.json();
                addMessageToUI('assistant', data.reply);
            } else {
                addMessageToUI('assistant', 'Error: Could not reach the AI.');
            }
        } catch (error) {
            removeLoadingIndicator();
            addMessageToUI('assistant', 'Error: Network failure.');
            console.error('Error sending message:', error);
        } finally {
            userInput.disabled = false;
            sendBtn.disabled = false;
            userInput.focus();
        }
    }

    sendBtn.addEventListener('click', sendMessage);

    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
});
