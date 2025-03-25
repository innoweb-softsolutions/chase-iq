import os
from pathlib import Path
from csv_processor import process_csv_file
from process_gemini import process_gemini_on_csv

# Define directories for raw data, processed CSVs, and final output
INPUT_DIR = "data"
PROCESSED_DIR = "processed"
FINAL_DIR = "final"

def main():
    # Ensure output directories exist
    Path(PROCESSED_DIR).mkdir(parents=True, exist_ok=True)
    Path(FINAL_DIR).mkdir(parents=True, exist_ok=True)

    processed_files = []
    # Stage 1: Process raw CSV files
    for file in os.listdir(INPUT_DIR):
        if file.lower().endswith('.csv'):
            input_file = os.path.join(INPUT_DIR, file)
            processed_file = process_csv_file(input_file, PROCESSED_DIR)
            processed_files.append(processed_file)

    # Stage 2: Use processed CSVs for Gemini role-checking
    for proc_file in processed_files:
        process_gemini_on_csv(proc_file, FINAL_DIR)

if __name__ == "__main__":
    main()
