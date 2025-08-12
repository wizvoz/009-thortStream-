# -*- coding: utf-8 -*-
"""
Filename:   build_database.py
Author:     Simon C, assisted by Dora
Version:    1.1
Date:       2025-08-12
Aim:        Generates the JSON data files required by the thortStream SPA.
            This script reads the master CSV report and all chat content,
            then outputs the consolidated database and search indexes.
Precursor:  Evolved from the 'build_website_content.py' script after the
            project architecture was refactored to a Single-Page Application.
"""

import os
import csv
import re
import json

# --- CONFIGURATION ---
BASE_DIR = os.getcwd()

# Input Paths
CSV_REPORT_PATH = os.path.join(BASE_DIR, 'output', 'reports', 'chat_analysis_report.csv')
ALL_CHATS_DIR = os.path.join(BASE_DIR, 'data', 'allchats')

# Output Path (directly into the live website folder)
WEBSITE_DATA_DIR = os.path.join(BASE_DIR, 'public')

def read_csv_data(filepath):
    """Reads the master CSV report into a list of dictionaries."""
    print(f"[INFO] Reading master report from: {filepath}")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return [row for row in csv.DictReader(f)]
    except FileNotFoundError:
        print(f"[FATAL] Master CSV report not found at '{filepath}'. Cannot continue.")
        print("[INFO] Please run the analysis script first: python src/02_analysis/analyze_gemini_chats.py")
        return None

def create_database_and_indexes(chat_data, output_dir):
    """
    Creates three JSON files: database.json, search_index_word.json,
    and search_index_full_text.json.
    """
    print("[INFO] Creating JSON database and search indexes...")
    database = {}
    word_index = {}
    full_text_index = {}
    stop_words = set(['a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from', 'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the', 'to', 'was', 'were', 'will', 'with'])
    
    for chat in chat_data:
        chat_id_str = chat.get('Chat ID')
        filename = chat.get('Matched Filename')
        folder = chat.get('Actual Folder')
        
        if not all([chat_id_str, filename, folder]): continue
        chat_id = int(chat_id_str)

        try:
            filepath = os.path.join(ALL_CHATS_DIR, folder, filename)
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            database[chat_id] = {
                'id': chat_id,
                'title': chat.get('Title', 'Untitled'),
                'msg_count': int(chat.get('Actual Msg Count', 0)),
                'filesize': int(chat.get('Filesize (bytes)', 0)),
                'content': content
            }

            lower_content = content.lower()
            full_text_index[chat_id] = lower_content

            tokens = set(re.findall(r'\b\w{2,}\b', lower_content)) - stop_words
            for token in tokens:
                if token not in word_index: word_index[token] = []
                word_index[token].append(chat_id)

        except FileNotFoundError:
            print(f"[WARNING] File not found while building database, skipping: {filepath}")
            continue

    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    with open(os.path.join(output_dir, 'database.json'), 'w') as f: json.dump(database, f)
    with open(os.path.join(output_dir, 'search_index_word.json'), 'w') as f: json.dump(word_index, f)
    with open(os.path.join(output_dir, 'search_index_full_text.json'), 'w') as f: json.dump(full_text_index, f)

    print(f"[SUCCESS] Database created ({len(database)} documents).")
    print(f"[SUCCESS] Word index created ({len(word_index)} tokens).")
    print(f"[SUCCESS] Full-text index created ({len(full_text_index)} documents).")

def main():
    print("--- Starting thortStream Database Builder ---")
    chat_data = read_csv_data(CSV_REPORT_PATH)
    if not chat_data: return

    valid_chats = [c for c in chat_data if c.get('Actual Msg Count') and c.get('Actual Msg Count') != 'N/A']
    
    # Generate the JSON database and indexes directly into the public folder
    create_database_and_indexes(valid_chats, WEBSITE_DATA_DIR)

    print(f"\n--- Database Build Complete ---")
    print(f"JSON data files have been updated in the '{WEBSITE_DATA_DIR}' directory.")

if __name__ == '__main__':
    main()
