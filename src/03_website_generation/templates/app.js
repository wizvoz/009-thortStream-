/**
 * @filename  app.js
 * @author    Simon C, assisted by Dora
 * @version   2.2 (Definitive Diagnostic)
 * @date      2025-08-12
 * @aim       The core client-side application for the thortStream archive.
 * @precursor Evolved from search.js and chat_page.js from the static site
 * generator version of the project.
 */
document.addEventListener('DOMContentLoaded', () => {
    // This is the most basic test. If this alert does not appear,
    // the browser is not executing the script's main body for some reason.
    alert("Dora Engine Initialized (Inside DOMContentLoaded)");

    const app = document.getElementById('app');
    let allChats = {};
    let wordIndex = {};
    let fullTextIndex = {};

    // --- TEMPLATES ---
    const mainLayoutTemplate = `
        <header class="text-center mb-10">
            <h1 class="text-5xl font-extrabold text-white">Stream of Consciousness</h1>
            <p class="text-gray-400 mt-2">A browsable archive of all conversations.</p>
            <div class="mt-4 space-x-4">
                <a href="docs/Project_Summary.html" class="text-blue-400 hover:underline">Project Summary</a>
                <a href="docs/Workflow_Manual.html" class="text-blue-400 hover:underline">Workflow Manual</a>
            </div>
            <div class="mt-6 max-w-xl mx-auto">
                <input type="search" id="search-input" placeholder="Search chats..." class="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-shadow">
                <div class="flex items-center justify-center mt-3 text-sm text-gray-400">
                    <input type="checkbox" id="pattern-search-toggle" class="mr-2 h-4 w-4 rounded bg-gray-700 border-gray-600 text-blue-500 focus:ring-blue-500">
                    <label for="pattern-search-toggle">Enable Pattern Search (slower, finds partial words)</label>
                </div>
            </div>
        </header>
        <div id="chat-list-container" class="space-y-4"></div>
        <div id="no-results" class="text-center text-gray-400 py-10 hidden"><p class="text-lg">No results found.</p></div>
        <footer class="text-center text-gray-500 mt-12 py-4"><p>thortStream Archive v2.2</p></footer>
    `;

    const chatViewTemplate = (chat, formattedContent) => `
        <header class="mb-8">
            <a href="#" id="back-to-index" class="text-blue-400 hover:text-blue-300 transition-colors">&larr; Back to Index</a>
            <h1 class="text-4xl font-bold mt-4 text-white">${escapeHtml(chat.title)}</h1>
            <p class="text-gray-400 text-sm mt-2">Chat ID: ${chat.id} | Messages: ${chat.msg_count} | Filesize: ${chat.filesize.toLocaleString()} bytes</p>
        </header>
        <details class="mb-8 p-6 bg-gray-800 rounded-lg border border-gray-700 cursor-pointer"><summary class="text-2xl font-semibold text-white list-none"><span class="marker">►</span> Associated Artifacts</summary><div class="mt-4"><p class="text-gray-400">This section is reserved for future artifacts.</p></div></details>
        <main id="chat-main-content" class="space-y-6">${formattedContent}</main>
        <footer class="text-center text-gray-500 mt-12 py-4"><p>thortStream Archive v2.2</p></footer>
        <div id="floating-nav" class="fixed bottom-5 right-5 space-y-2"><button id="next-occurrence-btn" title="Next Occurrence (N)" class="hidden w-14 h-14 bg-blue-600 text-white rounded-full shadow-lg hover:bg-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-400 flex items-center justify-center text-lg font-bold">Next</button><button id="back-to-top-btn" title="Back to Top" class="w-14 h-14 bg-gray-700 text-white rounded-full shadow-lg hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-500 flex items-center justify-center">&uarr;</button></div>
    `;

    // --- UTILITY FUNCTIONS ---
    const escapeHtml = (str) => str.replace(/[&<>"']/g, (match) => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[match]));
    const formatChatContent = (rawText) => {
        if (!rawText) return "<p class='text-red-400'>Could not load chat content.</p>";
        const escapedText = escapeHtml(rawText);
        const parts = escapedText.split(/(## (?:PROMPT|RESPONSE) ##)/);
        let htmlContent = "";
        for (let i = 1; i < parts.length; i += 2) {
            const marker = parts[i];
            const content = parts[i + 1].trim().replace(/\n/g, '<br>');
            if (marker.includes("PROMPT")) {
                htmlContent += `<div class="p-4 bg-blue-900/30 border border-blue-800 rounded-lg"><h3 class="font-semibold text-blue-300 mb-2">Simon's Prompt</h3><div class="prose prose-invert max-w-none text-gray-300">${content}</div></div>`;
            } else if (marker.includes("RESPONSE")) {
                htmlContent += `<div class="p-4 bg-gray-800/50 border border-gray-700 rounded-lg"><h3 class="font-semibold text-gray-300 mb-2">Dora's Response</h3><div class="prose prose-invert max-w-none text-gray-200">${content}</div></div>`;
            }
        }
        return htmlContent || `<p>${escapedText.replace(/\n/g, '<br>')}</p>`;
    };
    
    // --- ROUTING & RENDERING ---
    const renderChatListView = (chatsToShow, query = '') => {
        app.innerHTML = mainLayoutTemplate;
        const container = document.getElementById('chat-list-container');
        const sortedChats = Object.values(chatsToShow).sort((a, b) => b.msg_count - a.msg_count);
        
        const highlightRegex = (query && query.length >= 3) ? new RegExp(`(${escapeRegExp(query)})`, 'gi') : null;

        container.innerHTML = sortedChats.map(chat => {
            let titleHtml = escapeHtml(chat.title);
            if (highlightRegex) {
                titleHtml = titleHtml.replace(highlightRegex, `<mark class="highlight">$1</mark>`);
            }
            return `
            <a href="#/chat/${chat.id}?q=${encodeURIComponent(query)}" data-chat-id="${chat.id}" class="block p-5 bg-gray-800 rounded-lg border border-gray-700 hover:bg-gray-700/80 hover:border-blue-600 transition-all duration-200">
                <div class="flex justify-between items-center">
                    <h2 class="text-xl font-bold text-white">${titleHtml}</h2>
                    <span class="text-lg font-semibold text-blue-400 bg-blue-900/50 px-3 py-1 rounded-full">${chat.msg_count} msgs</span>
                </div>
            </a>`
        }).join('');
        
        setupSearchListeners();
        document.getElementById('search-input').value = query;
    };

    const renderChatDetailView = (chatId) => {
        const chat = allChats[chatId];
        if (!chat) { renderChatListView(allChats); return; }
        
        const params = new URLSearchParams(window.location.hash.split('?')[1] || '');
        const searchQuery = params.get('q');
        
        let formattedContent = formatChatContent(chat.content);
        app.innerHTML = chatViewTemplate(chat, formattedContent);
        
        requestAnimationFrame(() => {
            document.getElementById('back-to-index').addEventListener('click', (e) => { e.preventDefault(); window.location.hash = ''; });
            setupChatPageListeners(searchQuery);
        });
    };

    const router = () => {
        const path = window.location.hash.slice(1).split('?')[0] || '/';
        const parts = path.split('/');
        
        if (parts[1] === 'chat' && parts[2]) {
            renderChatDetailView(parts[2]);
        } else {
            const params = new URLSearchParams(window.location.hash.split('?')[1] || '');
            const searchQuery = params.get('q') || '';
            renderChatListView(allChats, searchQuery);
        }
    };

    // --- EVENT LISTENERS & LOGIC ---
    const setupSearchListeners = () => {
        const searchInput = document.getElementById('search-input');
        const patternToggle = document.getElementById('pattern-search-toggle');
        const chatListContainer = document.getElementById('chat-list-container');
        const noResultsMessage = document.getElementById('no-results');
        const chatLinks = Array.from(chatListContainer.getElementsByTagName('a'));
        let isPatternMode = false;

        patternToggle.addEventListener('change', () => { isPatternMode = patternToggle.checked; searchInput.dispatchEvent(new Event('input')); });
        
        const performSearch = () => {
            const query = searchInput.value.toLowerCase().trim();
            let matchedIds;

            if (isPatternMode) {
                if (query.length < 3) { matchedIds = new Set(Object.keys(allChats).map(Number)); }
                else { matchedIds = new Set(); for (const id in fullTextIndex) { if (fullTextIndex[id].includes(query)) matchedIds.add(Number(id)); } }
            } else {
                const terms = query.split(/\s+/).filter(term => term.length > 1);
                if (terms.length === 0) { matchedIds = new Set(Object.keys(allChats).map(Number)); }
                else { const idSets = terms.map(term => new Set(wordIndex[term] || [])); matchedIds = idSets.reduce((a, b) => new Set([...a].filter(x => b.has(x)))); }
            }

            let resultsFound = false;
            chatLinks.forEach(link => {
                const chatId = parseInt(link.dataset.chatId, 10);
                const titleElement = link.querySelector('h2');
                let titleHtml = escapeHtml(allChats[chatId].title);
                
                const originalHref = `#/chat/${chatId}`;
                link.href = query ? `${originalHref}?q=${encodeURIComponent(query)}` : originalHref;

                if (matchedIds.has(chatId)) {
                    link.style.display = 'block';
                    resultsFound = true;
                    if (query.length >= 3) {
                        const highlightRegex = new RegExp(`(${escapeRegExp(query)})`, 'gi');
                        titleHtml = titleHtml.replace(highlightRegex, `<mark class="highlight">$1</mark>`);
                    }
                } else {
                    link.style.display = 'none';
                }
                titleElement.innerHTML = titleHtml;
            });
            noResultsMessage.classList.toggle('hidden', resultsFound || query.length === 0);
        };
        searchInput.addEventListener('input', performSearch);
    };

    const setupChatPageListeners = (searchQuery) => {
        const mainContent = document.getElementById('chat-main-content');
        const backToTopBtn = document.getElementById('back-to-top-btn');
        const nextOccurrenceBtn = document.getElementById('next-occurrence-btn');
        const floatingNav = document.getElementById('floating-nav');
        let currentHighlightIndex = -1;
        let highlights = [];

        if (searchQuery && mainContent) {
            const query = searchQuery.toLowerCase();
            const messageBlocks = mainContent.querySelectorAll('div.p-4');
            
            messageBlocks.forEach(block => {
                if (block.textContent.toLowerCase().includes(query)) {
                    block.classList.add('highlight');
                    highlights.push(block);
                }
            });

            if (highlights.length > 0) {
                nextOccurrenceBtn.classList.remove('hidden');
                currentHighlightIndex = 0;
                highlights[0].classList.add('current-highlight');
                setTimeout(() => {
                    highlights[0].scrollIntoView({ behavior: 'smooth', block: 'center' });
                }, 100);
            }
        }

        const scrollToNext = () => {
            if (highlights.length === 0) return;
            highlights[currentHighlightIndex].classList.remove('current-highlight');
            currentHighlightIndex = (currentHighlightIndex + 1) % highlights.length;
            highlights[currentHighlightIndex].classList.add('current-highlight');
            highlights[currentHighlightIndex].scrollIntoView({ behavior: 'smooth', block: 'center' });
        };

        window.addEventListener('scroll', () => floatingNav.classList.toggle('hidden', window.scrollY < 200));
        backToTopBtn.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
        nextOccurrenceBtn.addEventListener('click', scrollToNext);
        document.addEventListener('keydown', (e) => { if (e.key === 'n' && highlights.length > 0) scrollToNext(); });
    };
    
    const escapeRegExp = (string) => {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); // $& means the whole matched string
    };

    // --- INITIALIZATION ---
    const init = async () => {
        try {
            const [dbRes, wordRes, fullTextRes] = await Promise.all([
                fetch('database.json'),
                fetch('search_index_word.json'),
                fetch('search_index_full_text.json')
            ]);
            allChats = await dbRes.json();
            wordIndex = await wordRes.json();
            fullTextIndex = await fullTextRes.json();
            
            window.addEventListener('hashchange', router);
            router(); // Initial route
        } catch (error) {
            app.innerHTML = `<div class="text-center text-red-400"><p><strong>Fatal Error:</strong> Could not load the archive database.</p><p>Please ensure you are running this from a local web server.</p><pre class="mt-4 text-left bg-gray-800 p-4 rounded">${error}</pre></div>`;
        }
    };

    init();
});
