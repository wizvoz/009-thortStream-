# **thortStream Workflow Manual**

This document outlines the complete workflow for the thortStream archive project.

## **Part 1: Data Acquisition**

1. **Get Metadata (get\_chat\_history.js):** Run the JavaScript snippet in the Gemini web console to produce chats.json.  
2. **Scrape Content (scrape\_chat\_content.py):** Run the Python scraper to download all chat files based on chats.json. This produces the raw chat files and the chatAnalysis.txt log.

## **Part 2: Data Consolidation & Analysis**

1. **Consolidate Files:** Manually gather all scraped chat files from various source locations and place them into data/allchats/consolidated.  
2. **Run Analysis (analyze\_gemini\_chats.py):** Execute this script from the project root. It will read all the source files and produce the master chat\_analysis\_report.csv in the output/reports directory.

## **Part 3: Website Generation**

1. **Build Website (build\_website\_content.py):** Execute this script from the project root. It reads the master CSV report and the templates in src/03\_website\_generation/templates to build the complete, searchable website in the public/ directory.

## **Part 4: Viewing the Archive**

1. **Start Local Server:** Navigate into the public/ directory in your terminal.  
2. Run the command: python \-m http.server  
3. **Browse:** Open your web browser and go to http://localhost:8000.