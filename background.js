// Handle installation and update events
chrome.runtime.onInstalled.addListener(function(details) {
    if (details.reason === "install") {
        console.log("Extension installed");
    } else if (details.reason === "update") {
        console.log("Extension updated");
    }
});

// Listen for messages from content script or popup
chrome.runtime.onMessage.addListener(function(request, sender, sendResponse) {
    if (request.action === "checkServer") {
        fetch('http://127.0.0.1:8000/')
            .then(response => response.json())
            .then(data => {
                sendResponse({ status: 'online' });
            })
            .catch(error => {
                sendResponse({ status: 'offline', error: error.message });
            });
        return true;
    }
}); 