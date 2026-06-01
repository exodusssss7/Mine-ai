document.addEventListener('DOMContentLoaded', () => {
    const chatBox = document.getElementById('chat-box');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const internetToggle = document.getElementById('internet-toggle');

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

    function showSearchAnimation(query) {
        const searchDiv = document.createElement('div');
        searchDiv.classList.add('search-indicator');
        searchDiv.id = 'search-indicator';
        searchDiv.innerHTML = `🌍 Searching the web for: <strong>"${query}"</strong>...`;
        chatBox.appendChild(searchDiv);
        scrollToBottom();
    }

    function removeSearchAnimation() {
        const searchDiv = document.getElementById('search-indicator');
        if (searchDiv) {
            searchDiv.remove();
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

        if (chatBox.children.length > 0 && chatBox.children[0].textContent.includes("awaken the AI")) {
            chatBox.children[0].remove();
        }

        userInput.value = '';
        userInput.disabled = true;
        sendBtn.disabled = true;
        internetToggle.disabled = true;

        addMessageToUI('user', text);
        addLoadingIndicator();

        try {
            // First step: send message to AI
            const response = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: text,
                    internet_enabled: internetToggle.checked
                })
            });

            removeLoadingIndicator();

            if (response.ok) {
                const data = await response.json();

                // If AI decided to search the web
                if (data.action === "search") {
                    showSearchAnimation(data.query);

                    // Second step: perform the search on the backend and get final answer
                    const searchResponse = await fetch('/resolve_search', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            query: data.query,
                            tool_call_id: data.tool_call_id
                        })
                    });

                    removeSearchAnimation();

                    if (searchResponse.ok) {
                        const finalData = await searchResponse.json();
                        addMessageToUI('assistant', finalData.reply);
                    } else {
                        addMessageToUI('assistant', 'Error: Failed to process search results.');
                    }

                } else {
                    // Standard reply
                    addMessageToUI('assistant', data.reply);
                }
            } else {
                addMessageToUI('assistant', 'Error: Could not reach the AI.');
            }
        } catch (error) {
            removeLoadingIndicator();
            removeSearchAnimation();
            addMessageToUI('assistant', 'Error: Network failure.');
            console.error('Error sending message:', error);
        } finally {
            userInput.disabled = false;
            sendBtn.disabled = false;
            internetToggle.disabled = false;
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
