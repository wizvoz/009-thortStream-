# -*- coding: utf-8 -*-
"""
Filename:   organize_misplaced_files.py
Author:     Simon C, assisted by Dora
Version:    1.0
Date:       2025-08-11
Description:
    A utility script to automate the organization of chat files. It reads the
    'misplaced_files_report.txt' and moves the specified files from their
    current folder to the correct 'Long' or 'Short' directory.
"""

import os
import re
import shutil

# --- CONFIGURATION ---
BASE_DIR = r'C:\Users\SimonC\theDen\Projects\007 WebApp Scraper\01_assets'
ALL_CHATS_DIR = os.path.join(BASE_DIR, 'allchats')
MISPLACED_FILES_REPORT_PATH = os.path.join(BASE_DIR, 'misplaced_files_report.txt')

# --- SCRIPT ---

def main():
    """Main function to read the report and move files."""
    print("--- Starting File Organization Script ---")

    if not os.path.exists(MISPLACED_FILES_REPORT_PATH):
        print(f"[ERROR] Report not found at: {MISPLACED_FILES_REPORT_PATH}")
        print("[INFO] Please run the main analysis script first.")
        return

    try:
        with open(MISPLACED_FILES_REPORT_PATH, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"[ERROR] Could not read report file: {e}")
        return

    # Regex to parse lines like: Move 'filename.txt' from 'Source' to 'Target'.
    move_pattern = re.compile(r"Move '(.*?)' from '(.*?)' to '(.*?)'\.")
    
    files_to_move = []
    for line in lines:
        match = move_pattern.match(line.strip())
        if match:
            filename, source_folder, target_folder = match.groups()
            files_to_move.append((filename, source_folder, target_folder))

    if not files_to_move:
        print("[INFO] Report is empty. No files to move.")
        print("--- Organization Complete ---")
        return

    print(f"[INFO] Found {len(files_to_move)} files to organize.")
    
    moved_count = 0
    error_count = 0
    for filename, source_folder, target_folder in files_to_move:
        source_path = os.path.join(ALL_CHATS_DIR, source_folder, filename)
        target_dir = os.path.join(ALL_CHATS_DIR, target_folder)
        target_path = os.path.join(target_dir, filename)

        print(f"\n[ACTION] Attempting to move '{filename}'...")
        print(f"  - From: {source_path}")
        print(f"  - To:   {target_path}")

        # Ensure source file exists
        if not os.path.exists(source_path):
            print(f"  [ERROR] Source file not found. Skipping.")
            error_count += 1
            continue
        
        # Ensure target directory exists
        os.makedirs(target_dir, exist_ok=True)

        # Move the file
        try:
            shutil.move(source_path, target_path)
            print(f"  [SUCCESS] File moved successfully.")
            moved_count += 1
        except Exception as e:
            print(f"  [ERROR] Failed to move file: {e}")
            error_count += 1

    print("\n--- Organization Summary ---")
    print(f"Successfully moved: {moved_count} file(s)")
    print(f"Errors encountered: {error_count} file(s)")
    print("--- Organization Complete ---")

if __name__ == '__main__':
    main()
