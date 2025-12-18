// Function to extract product information from Amazon page
function extractProductInfo() {
    const productInfo = {
        name: document.getElementById('productTitle')?.textContent.trim(),
        price: document.querySelector('.a-price-whole')?.textContent.trim(),
        currency: document.querySelector('.a-price-symbol')?.textContent.trim(),
        description: document.getElementById('productDescription')?.textContent.trim() ||
                    document.getElementById('feature-bullets')?.textContent.trim(),
        url: window.location.href
    };

    // Extract ASIN from URL
    const asinMatch = window.location.pathname.match(/\/dp\/([A-Z0-9]{10})/);
    if (asinMatch) {
        productInfo.asin = asinMatch[1];
    }

    // Extract rating
    const ratingElement = document.querySelector('.a-icon-alt');
    if (ratingElement) {
        productInfo.rating = ratingElement.textContent.trim();
    }

    // Extract review count
    const reviewCountElement = document.getElementById('acrCustomerReviewText');
    if (reviewCountElement) {
        productInfo.reviewCount = reviewCountElement.textContent.trim();
    }

    // Extract sustainability features
    const sustainabilitySection = Array.from(document.querySelectorAll('*')).find(
        element => element.textContent.toLowerCase().includes('sustainability features')
    );
    if (sustainabilitySection) {
        const features = [];
        const parent = sustainabilitySection.closest('div');
        if (parent) {
            const listItems = parent.querySelectorAll('li, p');
            listItems.forEach(item => {
                const text = item.textContent.trim();
                if (text) features.push(text);
            });
        }
        productInfo.sustainabilityFeatures = features;
        productInfo.sustainabilityCertified = true;
    }

    return productInfo;
}

// Create and inject the chatbot UI
function createChatbotUI() {
    // Create the floating button
    const floatingButton = document.createElement('div');
    floatingButton.innerHTML = `
        <div id="eco-chatbot-button" style="
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 60px;
            height: 60px;
            background: #4CAF50;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            z-index: 10000;
            transition: transform 0.3s;
        ">
            <svg width="30" height="30" viewBox="0 0 24 24" fill="white">
                <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/>
            </svg>
        </div>
    `;

    // Create the chat window
    const chatWindow = document.createElement('div');
    chatWindow.innerHTML = `
        <div id="eco-chatbot-window" style="
            position: fixed;
            bottom: 90px;
            right: 20px;
            width: 350px;
            height: 500px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.15);
            z-index: 10000;
            display: none;
            flex-direction: column;
            overflow: hidden;
        ">
            <div class="chat-header" style="
                background: #4CAF50;
                color: white;
                padding: 15px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                cursor: move;
            ">
                <h3 style="margin: 0">EcoSmart Assistant</h3>
                <div style="display: flex; gap: 10px;">
                    <button id="eco-chatbot-minimize" style="
                        background: none;
                        border: none;
                        color: white;
                        cursor: pointer;
                        font-size: 20px;
                    ">−</button>
                </div>
            </div>
            <div id="eco-chatbot-messages" style="
                flex: 1;
                overflow-y: auto;
                padding: 15px;
                background: #f5f5f5;
            "></div>
            <div style="
                padding: 15px;
                background: white;
                border-top: 1px solid #eee;
                display: flex;
                gap: 10px;
            ">
                <input id="eco-chatbot-input" type="text" placeholder="Ask about eco-friendly products..." style="
                    flex: 1;
                    padding: 8px 12px;
                    border: 1px solid #ddd;
                    border-radius: 20px;
                    outline: none;
                ">
                <button id="eco-chatbot-send" style="
                    background: #4CAF50;
                    color: white;
                    border: none;
                    padding: 8px 15px;
                    border-radius: 20px;
                    cursor: pointer;
                ">Send</button>
            </div>
        </div>
    `;

    document.body.appendChild(floatingButton);
    document.body.appendChild(chatWindow);

    // Make the window draggable
    const header = chatWindow.querySelector('.chat-header');
    const window = document.getElementById('eco-chatbot-window');
    let isDragging = false;
    let currentX;
    let currentY;
    let initialX;
    let initialY;
    let xOffset = 0;
    let yOffset = 0;

    header.addEventListener('mousedown', dragStart);
    document.addEventListener('mousemove', drag);
    document.addEventListener('mouseup', dragEnd);

    function dragStart(e) {
        initialX = e.clientX - xOffset;
        initialY = e.clientY - yOffset;

        if (e.target === header) {
            isDragging = true;
        }
    }

    function drag(e) {
        if (isDragging) {
            e.preventDefault();
            currentX = e.clientX - initialX;
            currentY = e.clientY - initialY;
            xOffset = currentX;
            yOffset = currentY;
            window.style.transform = `translate(${currentX}px, ${currentY}px)`;
        }
    }

    function dragEnd() {
        isDragging = false;
    }

    // Add event listeners
    const button = document.getElementById('eco-chatbot-button');
    const minimize = document.getElementById('eco-chatbot-minimize');
    const input = document.getElementById('eco-chatbot-input');
    const send = document.getElementById('eco-chatbot-send');
    const messages = document.getElementById('eco-chatbot-messages');

    button.addEventListener('click', () => {
        window.style.display = 'flex';
        button.style.transform = 'scale(0)';
    });

    minimize.addEventListener('click', () => {
        window.style.display = 'none';
        button.style.transform = 'scale(1)';
    });

    function addMessage(text, isUser) {
        const message = document.createElement('div');
        message.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
        message.style.cssText = `
            margin-bottom: 10px;
            padding: 10px 15px;
            border-radius: 10px;
            max-width: 85%;
            ${isUser ? `
                background: #e3f2fd;
                margin-left: auto;
            ` : `
                background: white;
                margin-right: auto;
            `}
        `;

        if (!isUser) {
            // Look for vendor suggestion pattern
            const vendorMatch = text.match(/Find local vendors for (\w+) products in Hyderabad/i);
            
            if (vendorMatch) {
                const category = vendorMatch[1].toLowerCase();
                
                // Split message into main content and vendor suggestion
                const [mainMessage] = text.split(/Find local vendors/i);
                
                // Create main message
                const messageText = document.createElement('div');
                messageText.style.marginBottom = '10px';
                messageText.innerHTML = mainMessage || text; // Fallback to full text if split fails
                message.appendChild(messageText);
                
                // Create vendor section with distinct styling
                const vendorSection = document.createElement('div');
                vendorSection.style.cssText = `
                    margin-top: 12px;
                    padding: 12px;
                    background: #f1f8e9;
                    border-radius: 8px;
                    border-left: 4px solid #4CAF50;
                `;
                
                // Add vendor header
                const vendorHeader = document.createElement('div');
                vendorHeader.style.cssText = `
                    font-weight: bold;
                    color: #2e7d32;
                    margin-bottom: 8px;
                    display: flex;
                    align-items: center;
                    gap: 6px;
                `;
                vendorHeader.innerHTML = '🏪 Local Eco-Friendly Vendors Available';
                vendorSection.appendChild(vendorHeader);
                
                // Add vendor description
                const vendorDesc = document.createElement('div');
                vendorDesc.style.cssText = `
                    font-size: 0.9em;
                    color: #1b5e20;
                    margin-bottom: 12px;
                `;
                vendorDesc.textContent = `Discover sustainable ${category} stores in Hyderabad`;
                vendorSection.appendChild(vendorDesc);

                // Add vendor button
                const vendorButton = document.createElement('button');
                vendorButton.innerHTML = '🗺️ View on Map';
                vendorButton.style.cssText = `
                    background: #4CAF50;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 20px;
                    cursor: pointer;
                    font-weight: 500;
                    display: flex;
                    align-items: center;
                    gap: 6px;
                    transition: all 0.3s ease;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                `;
                vendorButton.onmouseover = () => {
                    vendorButton.style.backgroundColor = '#45a049';
                    vendorButton.style.transform = 'translateY(-1px)';
                    vendorButton.style.boxShadow = '0 4px 8px rgba(0,0,0,0.15)';
                };
                vendorButton.onmouseout = () => {
                    vendorButton.style.backgroundColor = '#4CAF50';
                    vendorButton.style.transform = 'translateY(0)';
                    vendorButton.style.boxShadow = '0 2px 5px rgba(0,0,0,0.1)';
                };
                vendorButton.onclick = () => showVendorMap(category);
                
                vendorSection.appendChild(vendorButton);
                message.appendChild(vendorSection);
            } else {
                // If no vendor match, just display the text
                message.innerHTML = text;
            }
        } else {
            // User message
            message.textContent = text;
        }

        const messages = document.getElementById('eco-chatbot-messages');
        messages.appendChild(message);
        messages.scrollTop = messages.scrollHeight;
    }

    async function sendMessage() {
        const text = input.value.trim();
        if (!text) return;

        input.value = '';
        addMessage(text, true);

        // Show loading message
        const loadingMessage = document.createElement('div');
        loadingMessage.className = 'message bot-message';
        loadingMessage.style.cssText = `
            margin-bottom: 10px;
            padding: 10px 15px;
            border-radius: 10px;
            background: white;
            margin-right: auto;
        `;
        loadingMessage.textContent = 'Thinking...';
        messages.appendChild(loadingMessage);
        messages.scrollTop = messages.scrollHeight;

        const productInfo = extractProductInfo();
        try {
            console.log('Sending query to API:', { query: text, context: productInfo });
            const response = await fetch('http://127.0.0.1:8000/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    query: text,
                    context: productInfo
                })
            });

            const data = await response.json();
            console.log('API Response:', data);

            // Remove loading message
            messages.removeChild(loadingMessage);

            if (data.error) {
                addMessage('Sorry, I encountered an error. Please try again.', false);
                return;
            }

            // Add the main response
            addMessage(data.answer, false);

            // Test vendor API separately
            const vendorMatch = data.answer.match(/Find local vendors for (\w+) products/i);
            if (vendorMatch) {
                const category = vendorMatch[1].toLowerCase();
                try {
                    const testResponse = await fetch(`http://127.0.0.1:8000/test-vendors/${category}`);
                    const testData = await testResponse.json();
                    console.log('Vendor API Test Response:', testData);
                } catch (error) {
                    console.error('Vendor API Test Error:', error);
                }
            }
        } catch (error) {
            console.error('API Error:', error);
            messages.removeChild(loadingMessage);
            addMessage('Sorry, I encountered an error. Please try again.', false);
        }
    }

    send.addEventListener('click', sendMessage);
    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });

    // Add welcome message
    addMessage('Hello! I\'m your EcoSmart Shopping Assistant. How can I help you find eco-friendly products today?', false);
}

// Initialize the chatbot UI
if (window.location.hostname.includes('amazon')) {
    createChatbotUI();
}

// Listen for messages from popup
chrome.runtime.onMessage.addListener(function(request, sender, sendResponse) {
    if (request.action === "getProductInfo") {
        const productInfo = extractProductInfo();
        sendResponse({productInfo: productInfo});
    }
    return true;
});

// Add this function after extractProductInfo()
function showVendorMap(category) {
    const mapWindow = window.open('', 'EcoVendors', 'width=800,height=600,status=0,scrollbars=0');
    
    // Create the map HTML content
    const mapContent = `
        <!DOCTYPE html>
        <html>
        <head>
            <title>Eco-Friendly Vendors in Hyderabad</title>
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
            <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
            <style>
                body { margin: 0; padding: 20px; font-family: Arial, sans-serif; }
                #map { height: 500px; border-radius: 10px; }
                .vendor-info { margin-top: 10px; padding: 10px; background: #f5f5f5; border-radius: 5px; }
                .vendor-name { font-weight: bold; color: #2c3e50; }
                .vendor-rating { color: #e67e22; }
                .vendor-type { color: #7f8c8d; }
            </style>
        </head>
        <body>
            <h2>Eco-Friendly ${category.charAt(0).toUpperCase() + category.slice(1)} Vendors in Hyderabad</h2>
            <div id="map"></div>
            <script>
                // Fetch vendor data from the API
                fetch('http://127.0.0.1:8000/vendors/${category}')
                    .then(response => response.json())
                    .then(data => {
                        const map = L.map('map').setView([data.center.lat, data.center.lng], 13);
                        
                        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                            attribution: '© OpenStreetMap contributors'
                        }).addTo(map);

                        // Add center marker
                        L.marker([data.center.lat, data.center.lng])
                            .bindPopup('Hyderabad City Center')
                            .addTo(map);

                        // Add vendor markers
                        data.vendors.forEach(vendor => {
                            const marker = L.marker([vendor.lat, vendor.lng])
                                .bindPopup(
                                    '<div class="vendor-info">' +
                                    '<div class="vendor-name">' + vendor.name + '</div>' +
                                    '<div class="vendor-rating">Rating: ' + vendor.rating + ' ⭐</div>' +
                                    '<div class="vendor-type">' + vendor.type + '</div>' +
                                    '</div>'
                                )
                                .addTo(map);
                        });
                    })
                    .catch(error => {
                        console.error('Error fetching vendor data:', error);
                        document.body.innerHTML += '<p style="color: red;">Error loading vendor data. Please try again.</p>';
                    });
            </script>
        </body>
        </html>
    `;
    
    mapWindow.document.write(mapContent);
    mapWindow.document.close();
} 