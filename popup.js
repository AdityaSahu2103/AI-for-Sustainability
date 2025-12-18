document.addEventListener('DOMContentLoaded', function() {
    const messageInput = document.getElementById('messageInput');
    const sendButton = document.getElementById('sendButton');
    const chatMessages = document.getElementById('chatMessages');
    const productContext = document.getElementById('productContext');

    let currentProductInfo = null;
    let serverOnline = false;

    // Check server status
    chrome.runtime.sendMessage({action: "checkServer"}, function(response) {
        serverOnline = response && response.status === 'online';
        if (!serverOnline) {
            addMessage("⚠️ Server is offline. Please make sure the backend server is running at http://127.0.0.1:8000", false);
            messageInput.disabled = true;
            sendButton.disabled = true;
        }
    });

    // Get current product info from the active tab
    chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
        if (tabs[0] && tabs[0].url && (tabs[0].url.includes('amazon.com') || tabs[0].url.includes('amazon.in'))) {
            chrome.tabs.sendMessage(tabs[0].id, {action: "getProductInfo"}, function(response) {
                if (response && response.productInfo) {
                    currentProductInfo = response.productInfo;
                    productContext.textContent = `Current product: ${response.productInfo.name}`;
                    productContext.style.display = 'block';
                }
            });
        } else {
            productContext.textContent = "Not on an Amazon product page";
            productContext.style.display = 'block';
        }
    });

    function addMessage(message, isUser) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
        
        // Handle markdown-style formatting
        if (!isUser) {
            message = message.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                           .replace(/\*(.*?)\*/g, '<em>$1</em>')
                           .replace(/- (.*?)(\n|$)/g, '• $1$2');
        }
        
        messageDiv.innerHTML = message;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    async function sendMessage() {
        if (!serverOnline) {
            addMessage("⚠️ Cannot send message: Server is offline", false);
            return;
        }

        const message = messageInput.value.trim();
        if (!message) return;

        // Disable input while processing
        messageInput.disabled = true;
        sendButton.disabled = true;

        // Add user message to chat
        addMessage(message, true);
        messageInput.value = '';

        // Show typing indicator
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message bot-message';
        typingDiv.textContent = 'Typing...';
        chatMessages.appendChild(typingDiv);

        // Prepare request payload
        const payload = {
            query: message,
            context: currentProductInfo || {}
        };

        try {
            const response = await fetch('http://127.0.0.1:8000/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            // Remove typing indicator
            chatMessages.removeChild(typingDiv);

            const data = await response.json();
            
            if (data.error) {
                addMessage('Sorry, I encountered an error. Please try again.', false);
            } else {
                addMessage(data.answer, false);
            }
        } catch (error) {
            // Remove typing indicator
            chatMessages.removeChild(typingDiv);
            
            console.error('Error:', error);
            addMessage('Sorry, I encountered an error. Please check if the server is running.', false);
            serverOnline = false;
        } finally {
            // Re-enable input
            messageInput.disabled = false;
            sendButton.disabled = false;
            messageInput.focus();
        }
    }

    // Event listeners
    sendButton.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Add welcome message
    addMessage('Hello! I\'m your EcoSmart Shopping Assistant. How can I help you find eco-friendly products today?', false);
}); 