# -*- coding: utf-8 -*-
"""
Filename:   analyze_gemini_chats.py
Author:     Simon C, assisted by Dora
Version:    1.9
Date:       2025-08-11
Description:
    This script analyzes scraped Google Gemini chat data. It consolidates data
    from a JSON file, a text log, and the filesystem.
    This version has been re-engineered to be "file-first". It adds any files
    found on disk that are NOT in the analysis log to the final report as
    "orphan" entries, ensuring a complete inventory.
"""

import os
import json
import csv
import re

# --- CONFIGURATION ---
# Adjust these paths to match your directory structure.
BASE_DIR = r'C:\Users\SimonC\theDen\Projects\007 WebApp Scraper\01_assets'
CHATS_JSON_PATH = os.path.join(BASE_DIR, 'chats.json')
ANALYSIS_LOG_PATH = os.path.join(BASE_DIR, 'chatAnalysis.txt')
ALL_CHATS_DIR = os.path.join(BASE_DIR, 'allchats')
OUTPUT_CSV_PATH = os.path.join(BASE_DIR, 'chat_analysis_report.csv')
RESCAPE_CONFIG_PATH = os.path.join(BASE_DIR, 'rescraping_config.json')
MISPLACED_FILES_REPORT_PATH = os.path.join(BASE_DIR, 'misplaced_files_report.txt')
# Assume scraped files have one of these extensions. Add others if needed.
EXPECTED_FILE_EXTENSIONS = ['.html', '.txt']


def count_messages_in_file(filepath):
    """
    Opens a chat file and counts the actual number of messages.
    """
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
    """
    Parses the chatAnalysis.txt log file to extract metadata for each chat.
    """
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
            'id': chat_id,
            'title_from_log': match.group(2),
            'logged_message_count': int(match.group(4)),
            'analysis_classification': match.group(3),
            'canvas_used': "[DEBUG] Canvas closed." in match.group(0),
            'anomaly_notes': []
        }
    
    print(f"[DEBUG] Parsed {len(chat_data)} entries from analysis log.")
    return chat_data

def add_json_data(chat_data, json_path):
    """
    Reads chats.json and adds the canonical title to the chat data.
    """
    print(f"[INFO] Reading JSON data from: {json_path}")
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            chats = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"[ERROR] Could not read or parse {json_path}: {e}")
        return

    json_map = {item['id']: item['title'] for item in chats}
    
    for chat_id, data in chat_data.items():
        if chat_id in json_map:
            data['title_from_json'] = json_map[chat_id]
        else:
            # This note is for chats in the log but not in the JSON.
            if 'ORPHAN_FILE' not in " ".join(data['anomaly_notes']):
                 data['anomaly_notes'].append(f"MISSING_METADATA: Chat ID {chat_id} not in chats.json.")
                 print(f"[WARNING] Chat ID {chat_id} found in log but not in chats.json.")

def scan_and_integrate_files(chat_data, chats_dir):
    """
    Scans directories, updates existing chat_data entries, and adds new
    entries for any "orphan" files not found in the original log.
    """
    print(f"[INFO] Scanning and integrating files from: {chats_dir}")
    if not os.path.isdir(chats_dir):
        print(f"[ERROR] '{os.path.basename(chats_dir)}' directory not found at: {chats_dir}")
        return

    id_pattern = re.compile(r'^(\d+)_')
    folders_to_scan = ['Short', 'Long', 'rescraped']
    print(f"[DEBUG] Scanning folders: {folders_to_scan}")

    for folder_name in folders_to_scan:
        folder_path = os.path.join(chats_dir, folder_name)
        if not os.path.isdir(folder_path):
            continue

        for filename in os.listdir(folder_path):
            match = id_pattern.match(filename)
            if not match:
                print(f"[WARNING] File without ID prefix found and ignored: {os.path.join(folder_name, filename)}")
                continue

            file_id = int(match.group(1))
            full_path = os.path.join(folder_path, filename)
            new_filesize = os.path.getsize(full_path)
            
            # **MODIFIED LOGIC**: Check if the file_id from the filename exists in our data.
            # If it exists, we update it. If not, we create it.
            
            # Case 1: The chat was in our log. Update its data.
            if file_id in chat_data:
                # Handle duplicates
                if 'matched_filename' in chat_data[file_id]:
                    old_filesize = chat_data[file_id]['filesize']
                    if new_filesize > old_filesize:
                        # Update with the larger file's data
                        chat_data[file_id].update({
                            'filesize': new_filesize,
                            'actual_folder': folder_name,
                            'matched_filename': filename,
                            'actual_message_count': count_messages_in_file(full_path)
                        })
                else:
                    # First time seeing a file for this logged chat
                    chat_data[file_id].update({
                        'filesize': new_filesize,
                        'actual_folder': folder_name,
                        'matched_filename': filename,
                        'actual_message_count': count_messages_in_file(full_path)
                    })
            
            # Case 2: The chat was NOT in our log. It's an orphan. Create a new entry.
            else:
                print(f"[INFO] Found orphan file: Chat ID {file_id} ('{filename}') not in analysis log. Adding to report.")
                chat_data[file_id] = {
                    'id': file_id,
                    'title_from_log': 'N/A',
                    'logged_message_count': 'N/A',
                    'analysis_classification': 'N/A',
                    'canvas_used': 'N/A', # Cannot know this without the log
                    'filesize': new_filesize,
                    'actual_folder': folder_name,
                    'matched_filename': filename,
                    'actual_message_count': count_messages_in_file(full_path),
                    'anomaly_notes': ['ORPHAN_FILE: File found on disk but not in analysis log.']
                }


def analyze_anomalies(chat_data):
    """
    Checks for missing files and misclassifications, adding specific notes.
    """
    print("[INFO] Analyzing data for anomalies...")
    for data in chat_data.values():
        # Check for files that were in the log but never found on disk.
        if 'matched_filename' not in data:
            data['anomaly_notes'].append("MISSING_FILE: Log entry exists but file not found.")

        # Check for classification mismatch.
        if data.get('analysis_classification') and data.get('actual_folder'):
            # Ignore this check for orphans, as they have no initial classification.
            if data['analysis_classification'] != 'N/A':
                if data['analysis_classification'].lower() != data['actual_folder'].lower():
                    note = (f"MISCLASSIFIED: Log says '{data['analysis_classification']}' "
                            f"but file is in '{data['actual_folder']}' folder.")
                    data['anomaly_notes'].append(note)

def write_csv_report(chat_data, output_path):
    """
    Writes the consolidated data and anomalies into a CSV file.
    """
    print(f"[INFO] Writing CSV report to: {output_path}")
    sorted_data = sorted(chat_data.values(), key=lambda x: x['id'])
    
    header = ['Chat ID', 'Title', 'Logged Msg Count', 'Actual Msg Count', 'Filesize (bytes)', 'Canvas Used', 
              'Log Classification', 'Actual Folder', 'Matched Filename', 'Anomalies']
    
    try:
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            for data in sorted_data:
                # Use the JSON title if available, otherwise use the filename for orphans
                title = data.get('title_from_json') or data.get('title_from_log')
                if not title or title == 'N/A':
                    title = data.get('matched_filename', 'N/A')

                writer.writerow([
                    data.get('id', 'N/A'),
                    title,
                    data.get('logged_message_count', 'N/A'),
                    data.get('actual_message_count', 'N/A'),
                    data.get('filesize', 'N/A'),
                    data.get('canvas_used', 'N/A'),
                    data.get('analysis_classification', 'N/A'),
                    data.get('actual_folder', 'N/A'),
                    data.get('matched_filename', 'N/A'),
                    " | ".join(data['anomaly_notes'])
                ])
        print(f"[SUCCESS] Report generated successfully!")
    except IOError as e:
        print(f"[ERROR] Could not write to CSV file: {e}")

def write_rescraping_config(chat_data, config_path):
    """
    Generates a JSON config file for chats that are still missing.
    """
    print(f"[INFO] Generating re-scraping config for MISSING files...")
    missing_ids = [
        str(data['id']) for data in chat_data.values() 
        if any("MISSING_FILE" in note for note in data['anomaly_notes'])
    ]
    missing_ids.sort(key=int)
    config = {"automation_mode": "hybrid", "chat_ids_to_scrape": ",".join(missing_ids), "delay_seconds": 3}
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
        print(f"[SUCCESS] Re-scraping config written to: {config_path}")
        print(f"[INFO] Found {len(missing_ids)} chats to re-scrape.")
    except IOError as e:
        print(f"[ERROR] Could not write to config file: {e}")

def write_misplaced_files_report(chat_data, report_path):
    """
    Generates a text file listing misclassified files and where to move them.
    """
    print(f"[INFO] Generating report for MISCLASSIFIED files...")
    misplaced_files = [
        data for data in chat_data.values() 
        if any("MISCLASSIFIED" in note for note in data['anomaly_notes'])
    ]
    try:
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("--- Misplaced Files Report ---\n\n")
            if not misplaced_files:
                f.write("No misclassified files were found.\n")
            else:
                f.write("The following files should be moved to the correct folder:\n\n")
                for data in misplaced_files:
                    target_folder = data['analysis_classification']
                    current_folder = data['actual_folder']
                    filename = data['matched_filename']
                    f.write(f"Move '{filename}' from '{current_folder}' to '{target_folder}'.\n")
        print(f"[SUCCESS] Misplaced files report written to: {report_path}")
        print(f"[INFO] Found {len(misplaced_files)} misplaced files.")
    except IOError as e:
        print(f"[ERROR] Could not write to misplaced files report: {e}")

def main():
    """Main function to orchestrate the analysis and reporting process."""
    print("--- Starting Gemini Chat Analysis ---")
    # Start with the data from the log file
    chat_data = parse_analysis_log(ANALYSIS_LOG_PATH)
    if not chat_data:
        print("[FATAL] Could not parse analysis log. Aborting.")
        return

    # Scan the filesystem to update existing entries and add orphan files
    scan_and_integrate_files(chat_data, ALL_CHATS_DIR)
    
    # Now that we have a complete list of all chats (logged and orphan),
    # enrich them with data from the JSON file.
    add_json_data(chat_data, CHATS_JSON_PATH)
    
    # Finally, perform the analysis on the complete dataset.
    analyze_anomalies(chat_data)
    
    # Write the three output files
    write_csv_report(chat_data, OUTPUT_CSV_PATH)
    write_rescraping_config(chat_data, RESCAPE_CONFIG_PATH)
    write_misplaced_files_report(chat_data, MISPLACED_FILES_REPORT_PATH)
    
    print("--- Analysis Complete ---")

if __name__ == '__main__':
    main()
