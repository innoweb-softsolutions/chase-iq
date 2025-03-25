import os
from pathlib import Path
from main import run_linkedin_scraper, run_snovio_email_finder, run_hunter_verification
from d7_integration import process_csv_file, process_gemini_on_csv

# Define directories used for D7 integration
PROCESSED_DIR = "processed"
FINAL_DIR = "final"

def integrated_d7_process(input_csv):
    """
    Runs the D7 integration steps on the given input CSV:
      1. Process the CSV file (mapping and filtering columns)
      2. Run Gemini role extraction to add the Role/Title field
    Returns the path to the final enriched CSV.
    """
    Path(PROCESSED_DIR).mkdir(parents=True, exist_ok=True)
    Path(FINAL_DIR).mkdir(parents=True, exist_ok=True)
    
    # Step 1: Process the CSV (map to the desired output schema)
    processed_csv = process_csv_file(input_csv, PROCESSED_DIR)
    
    # Step 2: Enrich the processed CSV with Gemini role extraction
    final_csv = process_gemini_on_csv(processed_csv, FINAL_DIR)
    return final_csv

def integrated_main():
    # 1. Run Sales Navigator scraper to get raw leads CSV
    print("[INFO] Starting Sales Navigator scraping...")
    sales_nav_csv = run_linkedin_scraper()
    if not sales_nav_csv:
        print("[ERROR] Sales Navigator scraping did not produce a CSV. Exiting.")
        return

    # 2. Run D7 integration on the scraped CSV to enrich with Role/Title
    print("[INFO] Running D7 integration on the scraped CSV...")
    enriched_csv = integrated_d7_process(sales_nav_csv)
    print(f"[INFO] D7 integration complete. Enriched CSV: {enriched_csv}")

    # 3. Run Snov.io email finder on the enriched CSV
    print("[INFO] Running Snov.io email finder on the enriched CSV...")
    snov_csv = run_snovio_email_finder(enriched_csv)
    if not snov_csv:
        print("[WARNING] Snov.io email finder did not complete successfully.")
        return

    # 4. Optionally run Hunter.io email verification
    print("[INFO] Running Hunter.io email verification on the final CSV...")
    if run_hunter_verification(snov_csv):
        print("[INFO] Hunter.io email verification complete.")
    else:
        print("[WARNING] Hunter.io email verification encountered issues.")
        
    print("[INFO] Integrated pipeline complete. Final CSV ready for use.")

if __name__ == "__main__":
    integrated_main()
