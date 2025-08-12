# -*- coding: utf-8 -*-
"""
Filename:   analyze_gemini_chats.py
Author:     Simon C, assisted by Dora
Version:    2.0
Date:       2025-08-12
Description:
    Core analysis engine. Reads raw data and logs to produce reports and
    actionable configs. This version is updated for the new project structure.
"""

import os
import json
import csv
import re

# --- CONFIGURATION (v2.0 - Updated for new project structure) ---
# This script assumes it is being run from the root of the '009_thortStream' project.
BASE_DIR = os.getcwd() # Get the current working directory as the base

# Input Paths
CHATS_JSON_PATH = os.path.join(BASE_DIR, 'data', 'metadata', 'chats.json')
ANALYSIS_LOG_PATH = os.path.join(BASE_DIR, 'output', 'logs', 'chatAnalysis.txt')
ALL_CHATS_DIR = os.path.join(BASE_DIR, 'data', 'allchats')

# Output Paths
OUTPUT_CSV_PATH = os.path.join(BASE_DIR, 'output', 'reports', 'chat_analysis_report.csv')
RESCAPE_CONFIG_PATH = os.path.join(BASE_DIR, 'output', 'configs', 'rescraping_config.json')
MISPLACED_FILES_REPORT_PATH = os.path.join(BASE_DIR, 'output', 'reports', 'misplaced_files_report.txt')

EXPECTED_FILE_EXTENSIONS = ['.html', '.txt']


def count_messages_in_file(filepath):
    """Opens a chat file and counts the actual number of messages."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        prompts = content.count('## PROMPT ##')
        responses = content.count('## RESPONSE ##')
        return prompts + responses
    except Exception as e:
        print(f"[ERROR] Could not read or process file {filepath}: {e}")
        return None

def parse_analysis_log(log_path):
    """Parses the chatAnalysis.txt log file to extract metadata for each chat."""
    print(f"[INFO] Parsing analysis log: {log_path}")
    chat_data = {}
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"[ERROR] Analysis log not found at: {log_path}")
        return {}
    pattern = re.compile(
        r"--- Analyzing Chat #(\d+).*?'(.*?)'.*?---\s*\n"
        r"(?:\[DEBUG\] Canvas closed\.\s*\n)?"
        r"\[RESULT\] (LONG|SHORT) chat detected \((\d+) messages\)",
        re.DOTALL
    )
    matches = pattern.finditer(content)
    for match in matches:
        chat_id = int(match.group(1))
        chat_data[chat_id] = {
            'id': chat_id, 'title_from_log': match.group(2),
            'logged_message_count': int(match.group(4)),
            'analysis_classification': match.group(3),
            'canvas_used': "[DEBUG] Canvas closed." in match.group(0),
            'anomaly_notes': []
        }
    print(f"[DEBUG] Parsed {len(chat_data)} entries from analysis log.")
    return chat_data

def scan_and_integrate_files(chat_data, chats_dir):
    """Scans directories, updates existing chat_data entries, and adds new entries for any "orphan" files."""
    print(f"[INFO] Scanning and integrating files from: {chats_dir}")
    if not os.path.isdir(chats_dir):
        print(f"[ERROR] '{os.path.basename(chats_dir)}' directory not found.")
        return
    id_pattern = re.compile(r'^(\d+)_')
    # We will look in the 'consolidated' folder where all chats were moved.
    for folder_name in ['consolidated', 'Long', 'Short', 'rescraped']:
        folder_path = os.path.join(chats_dir, folder_name)
        if not os.path.isdir(folder_path): continue
        for filename in os.listdir(folder_path):
            match = id_pattern.match(filename)
            if not match: continue
            file_id = int(match.group(1))
            full_path = os.path.join(folder_path, filename)
            new_filesize = os.path.getsize(full_path)
            if file_id in chat_data:
                if 'matched_filename' not in chat_data[file_id] or new_filesize > chat_data[file_id].get('filesize', 0):
                    chat_data[file_id].update({
                        'filesize': new_filesize, 'actual_folder': folder_name,
                        'matched_filename': filename, 'actual_message_count': count_messages_in_file(full_path)
                    })
            else:
                chat_data[file_id] = {
                    'id': file_id, 'filesize': new_filesize, 'actual_folder': folder_name,
                    'matched_filename': filename, 'actual_message_count': count_messages_in_file(full_path),
                    'anomaly_notes': ['ORPHAN_FILE: File found on disk but not in analysis log.']
                }

def add_json_data(chat_data, json_path):
    """Reads chats.json and adds the canonical title to the chat data."""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            json_map = {int(item['id']): item['title'] for item in json.load(f)}
        for chat_id, data in chat_data.items():
            if chat_id in json_map:
                data['title_from_json'] = json_map[chat_id]
            elif 'ORPHAN_FILE' not in " ".join(data.get('anomaly_notes', [])):
                data.setdefault('anomaly_notes', []).append(f"MISSING_METADATA: Chat ID {chat_id} not in chats.json.")
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"[WARNING] Could not read or process {json_path}. Titles may be missing from report.")

def analyze_anomalies(chat_data):
    """Checks for missing files and misclassifications."""
    for data in chat_data.values():
        if 'matched_filename' not in data:
            data.setdefault('anomaly_notes', []).append("MISSING_FILE: Log entry exists but file not found.")
        classification = data.get('analysis_classification')
        folder = data.get('actual_folder')
        if classification and folder and classification != 'N/A' and classification.lower() != folder.lower():
            data.setdefault('anomaly_notes', []).append(f"MISCLASSIFIED: Log says '{classification}' but file is in '{folder}' folder.")

def write_reports(chat_data):
    """Generates all output files (CSV, JSON config, TXT report)."""
    # Ensure output directories exist
    os.makedirs(os.path.dirname(OUTPUT_CSV_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(RESCAPE_CONFIG_PATH), exist_ok=True)
    
    sorted_data = sorted(chat_data.values(), key=lambda x: x['id'])
    header = ['Chat ID', 'Title', 'Logged Msg Count', 'Actual Msg Count', 'Filesize (bytes)', 'Canvas Used', 'Log Classification', 'Actual Folder', 'Matched Filename', 'Anomalies']
    with open(OUTPUT_CSV_PATH, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for data in sorted_data:
            title = data.get('title_from_json') or data.get('title_from_log') or data.get('matched_filename', 'N/A')
            writer.writerow([
                data.get('id', 'N/A'), title, data.get('logged_message_count', 'N/A'),
                data.get('actual_message_count', 'N/A'), data.get('filesize', 'N/A'), data.get('canvas_used', 'N/A'),
                data.get('analysis_classification', 'N/A'), data.get('actual_folder', 'N/A'),
                data.get('matched_filename', 'N/A'), " | ".join(data.get('anomaly_notes', []))
            ])
    print(f"[SUCCESS] Master report generated: {OUTPUT_CSV_PATH}")

    missing_ids = sorted([str(d['id']) for d in chat_data.values() if any("MISSING_FILE" in n for n in d.get('anomaly_notes', []))], key=int)
    with open(RESCAPE_CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump({"automation_mode": "hybrid", "chat_ids_to_scrape": ",".join(missing_ids), "delay_seconds": 3}, f, indent=4)
    print(f"[SUCCESS] Rescrape config generated: {RESCAPE_CONFIG_PATH} ({len(missing_ids)} IDs)")

    misplaced_files = [d for d in chat_data.values() if any("MISCLASSIFIED" in n for n in d.get('anomaly_notes', []))]
    with open(MISPLACED_FILES_REPORT_PATH, 'w', encoding='utf-8') as f:
        f.write("--- Misplaced Files Report ---\n\n")
        if not misplaced_files:
            f.write("No misclassified files were found.\n")
        else:
            for data in misplaced_files:
                f.write(f"Move '{data['matched_filename']}' from '{data['actual_folder']}' to '{data['analysis_classification']}'.\n")
    print(f"[SUCCESS] Misplaced files report generated: {MISPLACED_FILES_REPORT_PATH} ({len(misplaced_files)} files)")

def main():
    """Main function to orchestrate the analysis and reporting process."""
    print("--- Starting Gemini Chat Analysis ---")
    chat_data = parse_analysis_log(ANALYSIS_LOG_PATH)
    scan_and_integrate_files(chat_data, ALL_CHATS_DIR)
    add_json_data(chat_data, CHATS_JSON_PATH)
    analyze_anomalies(chat_data)
    write_reports(chat_data)
    print("--- Analysis Complete ---")

if __name__ == '__main__':
    main()
