# -*- coding: utf-8 -*-
"""
Filename:   build_website_content.py
Author:     Simon C, assisted by Dora
Version:    1.5
Date:       2025-08-12
Description:
    A static site content builder. This version fixes a critical bug where
    the search index was being generated incorrectly, resulting in an empty
    index file.
"""

import os
import csv
import shutil
import re
import html
import json

# --- CONFIGURATION ---
BASE_DIR = os.getcwd()

# Input Paths
CSV_REPORT_PATH = os.path.join(BASE_DIR, 'output', 'reports', 'chat_analysis_report.csv')
ALL_CHATS_DIR = os.path.join(BASE_DIR, 'data', 'allchats')
SOURCE_TEMPLATES_DIR = os.path.join(BASE_DIR, 'src', '03_website_generation', 'templates')
SOURCE_DOCS_DIR = os.path.join(BASE_DIR, 'src', 'docs')

# Output Path
WEBSITE_OUTPUT_DIR = os.path.join(BASE_DIR, 'public')

def read_csv_data(filepath):
    """Reads the master CSV report into a list of dictionaries."""
    print(f"[INFO] Reading master report from: {filepath}")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return [row for row in reader]
    except FileNotFoundError:
        print(f"[FATAL] Master CSV report not found at '{filepath}'. Cannot continue.")
        return None

def format_chat_content(raw_text):
    """Formats the raw chat text into styled HTML."""
    if not raw_text: return "<p class='text-red-400'>Could not load chat content.</p>"
    escaped_text = html.escape(raw_text)
    parts = re.split(r'(## (?:PROMPT|RESPONSE) ##)', escaped_text)
    html_content = ""
    for i in range(1, len(parts), 2):
        marker, content = parts[i], parts[i+1].strip().replace('\n', '<br>')
        if "PROMPT" in marker:
            html_content += f'<div class="p-4 bg-blue-900/30 border border-blue-800 rounded-lg"><h3 class="font-semibold text-blue-300 mb-2">Simon\'s Prompt</h3><div class="prose prose-invert max-w-none text-gray-300">{content}</div></div>'
        elif "RESPONSE" in marker:
            html_content += f'<div class="p-4 bg-gray-800/50 border border-gray-700 rounded-lg"><h3 class="font-semibold text-gray-300 mb-2">Dora\'s Response</h3><div class="prose prose-invert max-w-none text-gray-200">{content}</div></div>'
    return html_content if html_content else f"<p>{escaped_text.replace('\n', '<br>')}</p>"

def create_search_index(chat_data, output_dir):
    """Creates a JSON search index from the chat content."""
    print("[INFO] Creating search index...")
    search_index = {}
    stop_words = set(['a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from', 'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the', 'to', 'was', 'were', 'will', 'with'])
    for chat in chat_data:
        chat_id, filename, folder = int(chat.get('Chat ID', 0)), chat.get('Matched Filename'), chat.get('Actual Folder')
        if not all([chat_id, filename, folder]): continue
        try:
            # **BUG FIX**: Use the 'folder' variable from the CSV, not a hardcoded path.
            filepath = os.path.join(ALL_CHATS_DIR, folder, filename)
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read().lower()
            tokens = set(re.findall(r'\b\w{2,}\b', content)) - stop_words
            for token in tokens:
                if token not in search_index: search_index[token] = []
                search_index[token].append(chat_id)
        except FileNotFoundError:
            print(f"[WARNING] File not found while building search index, skipping: {filepath}")
            continue
    with open(os.path.join(output_dir, 'search_index.json'), 'w', encoding='utf-8') as f:
        json.dump(search_index, f)
    print(f"[SUCCESS] Search index created with {len(search_index)} tokens.")

def main():
    print("--- Starting thortStream Archive Builder ---")
    chat_data = read_csv_data(CSV_REPORT_PATH)
    if not chat_data: return

    valid_chats = [c for c in chat_data if c.get('Actual Msg Count') and c.get('Actual Msg Count') != 'N/A']
    sorted_chats = sorted(valid_chats, key=lambda x: int(x['Actual Msg Count']), reverse=True)
    
    # Setup output directories
    if os.path.exists(WEBSITE_OUTPUT_DIR): shutil.rmtree(WEBSITE_OUTPUT_DIR)
    os.makedirs(WEBSITE_OUTPUT_DIR)
    chats_output_dir = os.path.join(WEBSITE_OUTPUT_DIR, 'chats')
    os.makedirs(chats_output_dir)
    docs_output_dir = os.path.join(WEBSITE_OUTPUT_DIR, 'docs')
    
    # Copy static files (JS, Docs)
    shutil.copy(os.path.join(SOURCE_TEMPLATES_DIR, 'search.js'), WEBSITE_OUTPUT_DIR)
    shutil.copy(os.path.join(SOURCE_TEMPLATES_DIR, 'chat_page.js'), WEBSITE_OUTPUT_DIR)
    shutil.copytree(SOURCE_DOCS_DIR, docs_output_dir)
    print(f"[INFO] Copied static assets and docs to output directory: {WEBSITE_OUTPUT_DIR}")

    # Read templates
    with open(os.path.join(SOURCE_TEMPLATES_DIR, 'index_template.html'), 'r') as f: index_template = f.read()
    with open(os.path.join(SOURCE_TEMPLATES_DIR, 'chat_page_template.html'), 'r') as f: chat_page_template = f.read()

    # Generate individual chat pages
    for chat in sorted_chats:
        chat_id, filename, folder = chat.get('Chat ID'), chat.get('Matched Filename'), chat.get('Actual Folder')
        if not all([chat_id, filename, folder]): continue
        raw_content = ""
        try:
            filepath = os.path.join(ALL_CHATS_DIR, folder, filename)
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f: raw_content = f.read()
        except FileNotFoundError: continue
        
        page_html = chat_page_template.replace('{title}', html.escape(chat.get('Title', 'Untitled')))
        page_html = page_html.replace('{chat_id}', chat_id)
        page_html = page_html.replace('{msg_count}', chat.get('Actual Msg Count', 'N/A'))
        page_html = page_html.replace('{filesize}', f"{int(chat.get('Filesize (bytes)', 0)):,}")
        page_html = page_html.replace('{content}', format_chat_content(raw_content))
        
        with open(os.path.join(chats_output_dir, f"{chat_id}.html"), 'w', encoding='utf-8') as f: f.write(page_html)
    print(f"[INFO] Generated {len(sorted_chats)} individual chat pages.")

    # Generate the search index
    create_search_index(sorted_chats, WEBSITE_OUTPUT_DIR)

    # Generate the index page content
    chat_list_html = ""
    for chat in sorted_chats:
        chat_list_html += f'<a href="chats/{chat.get("Chat ID")}.html" data-chat-id="{chat.get("Chat ID")}" class="block p-5 bg-gray-800 rounded-lg border border-gray-700 hover:bg-gray-700/80 hover:border-blue-600 transition-all duration-200"><div class="flex justify-between items-center"><h2 class="text-xl font-bold text-white">{html.escape(chat.get("Title"))}</h2><span class="text-lg font-semibold text-blue-400 bg-blue-900/50 px-3 py-1 rounded-full">{chat.get("Actual Msg Count")} msgs</span></div></a>\n'
    
    final_index_html = index_template.replace('{chat_list}', chat_list_html)
    with open(os.path.join(WEBSITE_OUTPUT_DIR, "index.html"), 'w', encoding='utf-8') as f: f.write(final_index_html)
    print("[INFO] Generated final index.html")

    print(f"\n--- Website Build Complete ---\nYou can now open the website by running 'python -m http.server' in the 'public' directory.")

if __name__ == '__main__':
    main()
