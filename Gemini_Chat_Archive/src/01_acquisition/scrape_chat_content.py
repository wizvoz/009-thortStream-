# -*- coding: utf-8 -*-
"""
Filename:   scrape_chat_content.py
Author:     Simon C, assisted by Dora
Version:    1.0
Date:       2025-08-11
Description:
    A web scraping script using Selenium to download the content of Google
    Gemini chats. It reads a 'chats.json' file for the list of URLs,
    navigates to each, saves the content, and generates a 'chatAnalysis.txt' log.
    It can also run in a targeted mode using 'rescraping_config.json'.
"""

import os
import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- CONFIGURATION ---
BASE_DIR = r'C:\Users\SimonC\theDen\Projects\007 WebApp Scraper\01_assets'
CHATS_JSON_PATH = os.path.join(BASE_DIR, 'chats.json')
RESCAPE_CONFIG_PATH = os.path.join(BASE_DIR, 'rescraping_config.json')
ALL_CHATS_DIR = os.path.join(BASE_DIR, 'allchats')
LOG_FILE_PATH = os.path.join(BASE_DIR, 'chatAnalysis.txt')

# Path to your chromedriver executable
# Download from: https://chromedriver.chromium.org/downloads
CHROME_DRIVER_PATH = r'C:\path\to\your\chromedriver.exe'

# --- SCRIPT ---

def initialize_driver():
    """Initializes and returns a Selenium WebDriver instance."""
    print("[INFO] Initializing WebDriver...")
    service = Service(executable_path=CHROME_DRIVER_PATH)
    options = webdriver.ChromeOptions()
    # Add any options you need, e.g., headless mode
    # options.add_argument('--headless')
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def login_to_google(driver):
    """Handles the initial login to a Google account."""
    print("[INFO] Navigating to Google login...")
    driver.get("https://accounts.google.com")
    print("\n" + "="*50)
    print("!! MANUAL ACTION REQUIRED !!")
    print("Please log in to your Google account in the browser window.")
    print("After you have successfully logged in, press Enter in this console to continue.")
    print("="*50 + "\n")
    input("Press Enter to continue...")
    print("[INFO] Assuming login was successful. Continuing script.")

def get_chats_to_scrape():
    """
    Determines which chats to scrape. Prioritizes the rescraping config,
    otherwise falls back to the main chats.json.
    """
    try:
        if os.path.exists(RESCAPE_CONFIG_PATH):
            with open(RESCAPE_CONFIG_PATH, 'r') as f:
                config = json.load(f)
            if config.get("chat_ids_to_scrape"):
                print(f"[INFO] Found rescraping config. Targeting specific IDs.")
                target_ids = {int(i) for i in config['chat_ids_to_scrape'].split(',')}
                with open(CHATS_JSON_PATH, 'r') as f:
                    all_chats = json.load(f)
                return [chat for chat in all_chats if chat['id'] in target_ids], True
    except Exception as e:
        print(f"[WARNING] Could not read or process rescraping config: {e}. Defaulting to full scrape.")

    print("[INFO] No valid rescraping config found. Scraping all chats from chats.json.")
    with open(CHATS_JSON_PATH, 'r') as f:
        return json.load(f), False

def main():
    """Main function to orchestrate the scraping process."""
    driver = initialize_driver()
    login_to_google(driver)

    chats, is_rescraping = get_chats_to_scrape()
    total_chats = len(chats)
    print(f"[INFO] Found {total_chats} chats to process.")

    with open(LOG_FILE_PATH, 'a', encoding='utf-8') as log_file:
        for i, chat in enumerate(chats):
            chat_id = chat['id']
            title = chat['title']
            url = chat['url']

            print(f"\n--- Analyzing Chat #{chat_id} ({i+1}/{total_chats}): '{title}' ---")
            log_file.write(f"\n--- Analyzing Chat #{chat_id} ({i+1}/{total_chats}): '{title}' ---\n")

            try:
                driver.get(url)
                # Wait for the main content area to be present
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '.conversation-container'))
                )
                time.sleep(2) # Allow content to settle

                # Simple classification based on message count
                messages = driver.find_elements(By.CSS_SELECTOR, '.message-content')
                msg_count = len(messages)
                classification = 'LONG' if msg_count >= 18 else 'SHORT'
                
                print(f"[RESULT] {classification} chat detected ({msg_count} messages).")
                log_file.write(f"[RESULT] {classification} chat detected ({msg_count} messages).\n")

                # Define save path based on classification or if re-scraping
                if is_rescraping:
                    save_dir = os.path.join(ALL_CHATS_DIR, 'rescraped')
                else:
                    save_dir = os.path.join(ALL_CHATS_DIR, classification)
                
                os.makedirs(save_dir, exist_ok=True)
                
                # Sanitize title for filename
                safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '.', '_')).rstrip()
                filename = f"{chat_id:03d}_{safe_title}.txt"
                filepath = os.path.join(save_dir, filename)

                # Extract and save text content
                page_text = driver.find_element(By.TAG_NAME, 'body').text
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(page_text)
                
                print(f"[SUCCESS] Saved chat to '{filepath}'")

            except Exception as e:
                print(f"[ERROR] Failed to process chat #{chat_id}: {e}")
                log_file.write(f"[ERROR] Failed to process chat #{chat_id}: {e}\n")

            time.sleep(2) # Be a good citizen

    print("\n[INFO] Scraping complete.")
    driver.quit()

if __name__ == '__main__':
    main()
