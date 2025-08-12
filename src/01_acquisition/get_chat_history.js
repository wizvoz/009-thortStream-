/**
 * Filename:   -++++++++++++++++
 * Author:     Simon C, assisted by Dora
 * Version:    1.0
 * Date:       2025-08-11
 * Description:
 * This JavaScript snippet is intended to be run in the developer console
 * of the Google Gemini web application. It scrapes the chat history sidebar,
 * extracts the title and URL for each conversation, assigns a sequential ID,
 * and outputs a JSON array to the console.
 */

(function() {
    console.log("[INFO] Starting chat history extraction...");

    // This selector targets the links in the chat history sidebar.
    // NOTE: This selector is subject to change if Google updates the Gemini UI.
    const historyLinks = document.querySelectorAll('a.history-link-item');

    if (historyLinks.length === 0) {
        console.error("[ERROR] No history links found. The selector may be outdated.");
        console.log("[DEBUG] Please check the Gemini UI and update the 'a.history-link-item' selector in the script.");
        return;
    }

    const chatHistory = [];
    let idCounter = 1;

    historyLinks.forEach(link => {
        // Find the title element within the link
        const titleElement = link.querySelector('.history-title-text');
        const title = titleElement ? titleElement.textContent.trim() : 'Untitled';
        
        // The href attribute contains the relative URL
        const relativeUrl = link.getAttribute('href');
        const fullUrl = `https://gemini.google.com${relativeUrl}`;

        chatHistory.push({
            id: idCounter++,
            title: title,
            url: fullUrl
        });
    });

    // Reverse the array so that the newest chats have the highest ID numbers,
    // which usually corresponds to how they appear visually (newest at top).
    const reversedHistory = chatHistory.reverse().map((item, index) => {
        item.id = index + 1;
        return item;
    });

    // Output the final JSON object to the console as a string.
    // The user can then easily copy this string.
    console.log("[SUCCESS] Extraction complete. Copy the JSON string below.");
    console.log(JSON.stringify(reversedHistory, null, 2));

})();
