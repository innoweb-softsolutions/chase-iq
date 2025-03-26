"""
LinkedIn Sales Navigator Scraper - Main Entry Point
"""
from src.scraper import LinkedInScraper
from src.ApolloScraper import ApolloScraper
import logging
import sys
import time
import os
import subprocess
import glob
import threading
import pandas as pd
import argparse
from pathlib import Path

# Set up logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(f"logs/scraper_{time.strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

def get_latest_csv_file(directory="output", prefix=None):
    """
    Get the latest CSV file from the specified directory with optional prefix.
    
    Args:
        directory (str): Path to the directory containing CSV files.
        prefix (str): Optional prefix to filter files
        
    Returns:
        str: Path to the latest CSV file.
    """
    pattern = os.path.join(directory, f"{prefix or ''}*.csv")
    list_of_files = glob.glob(pattern)
    if not list_of_files:
        return None
    latest_file = max(list_of_files, key=os.path.getctime)
    logging.info(f"Using latest file: {latest_file}")
    return latest_file

def run_linkedin_scraper():
    """Run LinkedIn Sales Navigator scraper and return the path to the saved CSV file."""
    logging.info("Starting LinkedIn Sales Navigator Scraper...")
    scraper = None
    csv_file = None
    
    try:
        # Initialize and login
        scraper = LinkedInScraper()
        scraper.login()
        from config.config import SALES_NAV_URL
        # Use the default search URL
        search_url = SALES_NAV_URL
        
        # Check if this URL was previously scraped and get starting page
        start_page = scraper.check_previous_scrape(search_url)
        
        # Extract profile links
        logging.info("Extracting profile links from search results...")
        profile_links = scraper.get_profile_links(start_page=start_page)
        
        if len(profile_links) == 0:
            logging.error("No profile links found. Exiting.")
            return None
            
        # Scrape individual profiles
        logging.info(f"Scraping {len(profile_links)} profiles...")
        leads = scraper.scrape_profiles(profile_links)
        
        # Save results to CSV
        if leads:
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            csv_file = f"output/linkedin_leads_{timestamp}.csv"
            scraper.save_to_csv(leads)
            
            # Try to get the latest CSV file if the save_to_csv doesn't return the path
            if csv_file is None:
                csv_file = get_latest_csv_file(prefix="linkedin_leads_")
                
            logging.info(f"Successfully scraped {len(leads)} leads and saved to {csv_file}")
        else:
            logging.error("No leads were collected.")
    
    except Exception as e:
        logging.error(f"An error occurred during LinkedIn scraping: {e}")
    
    finally:
        # Clean up
        if scraper:
            scraper.cleanup()
        logging.info("LinkedIn scraping complete.")
    
    return csv_file

def run_apollo_scraper():
    """Run Apollo scraper and return the path to the saved CSV file."""
    logging.info("Running Apollo Scraper...")
    try:
        ApolloScraper()
        # The Apollo scraper typically saves files with a pattern like 'ApolloCleaned_Filtered.csv'
        csv_file = get_latest_csv_file(prefix="ApolloCleaned_Filtered")
        if csv_file:
            logging.info(f"Apollo scraping complete. Results saved to {csv_file}")
        else:
            logging.warning("Apollo scraping complete, but couldn't locate the output file.")
        return csv_file
    except Exception as e:
        logging.error(f"An error occurred during Apollo scraping: {e}")
        return None

def run_snovio_email_finder(csv_file):
    """Run Snov.io email finder on a CSV file."""
    if csv_file is None:
        logging.warning("No CSV file provided for Snov.io processing")
        return None
        
    logging.info(f"Running Snov.io email finder on {csv_file}...")
    try:
        # Get path to snov_email_finder.py
        script_dir = os.path.dirname(os.path.abspath(__file__))
        snov_script_path = os.path.join(script_dir, "src", "snov_email_finder.py")
        
        if not os.path.exists(snov_script_path):
            # Try alternative path
            snov_script_path = os.path.join(script_dir, "src", "utils", "snov_email_finder.py")
            
        if not os.path.exists(snov_script_path):
            logging.error("Could not find Snov.io email finder script")
            return None
            
        csv_filename = os.path.basename(csv_file)
        subprocess.run(["python", snov_script_path, "--file", csv_filename], check=True)
        logging.info("Snov.io email finder complete.")
        
        # Run email pattern generation as fallback
        pattern_script_path = os.path.join(script_dir, "src", "email_pattern_generator.py")
        if os.path.exists(pattern_script_path):
            logging.info("Running email pattern generation as fallback...")
            subprocess.run(["python", pattern_script_path, "--file", csv_filename], check=True)
            logging.info("Email pattern generation complete.")
            
        return csv_file
    except Exception as e:
        logging.error(f"Error during Snov.io processing: {e}")
        return None

def run_hunter_verification(csv_file):
    """Run Hunter.io email verification on a CSV file."""
    if csv_file is None:
        logging.warning("No CSV file provided for Hunter.io verification")
        return False
    
    logging.info(f"Verifying emails with Hunter.io for {csv_file}...")
    try:
        # Get path to email_verifier.py
        script_dir = os.path.dirname(os.path.abspath(__file__))
        verifier_script_path = os.path.join(script_dir, "src", "email_verifier.py")
        
        if not os.path.exists(verifier_script_path):
            # Try alternative path
            verifier_script_path = os.path.join(script_dir, "src", "utils", "email_verifier.py")
            
        if not os.path.exists(verifier_script_path):
            logging.error("Could not find Hunter.io email verifier script")
            return False
            
        csv_filename = os.path.basename(csv_file)
        subprocess.run(["python", verifier_script_path, "--file", csv_filename], check=True)
        logging.info("Email verification complete.")
        return True
    except Exception as e:
        logging.error(f"Error during Hunter.io verification: {e}")
        return False

def merge_csv_files(linkedin_csv, apollo_csv, output_file="output/merged_leads.csv"):
    """Merge LinkedIn and Apollo CSV files."""
    # Initialize with empty DataFrames in case one source fails
    linkedin_df = pd.DataFrame()
    apollo_df = pd.DataFrame()
    
    # Read LinkedIn CSV if available
    if linkedin_csv and os.path.exists(linkedin_csv):
        try:
            linkedin_df = pd.read_csv(linkedin_csv)
            linkedin_df['Source'] = 'LinkedIn'
            logging.info(f"Read {len(linkedin_df)} rows from LinkedIn CSV")
        except Exception as e:
            logging.error(f"Error reading LinkedIn CSV: {e}")
    
    # Read Apollo CSV if available
    if apollo_csv and os.path.exists(apollo_csv):
        try:
            apollo_df = pd.read_csv(apollo_csv)
            apollo_df['Source'] = 'Apollo'
            logging.info(f"Read {len(apollo_df)} rows from Apollo CSV")
        except Exception as e:
            logging.error(f"Error reading Apollo CSV: {e}")
    
    # If both files are empty/unavailable, return None
    if linkedin_df.empty and apollo_df.empty:
        logging.warning("Both CSV files are empty or couldn't be read. Cannot merge.")
        return None
    
    try:
        # Standardize column names for LinkedIn data
        if not linkedin_df.empty:
            linkedin_columns = {'Name': 'Name', 'Title': 'Title', 'Company': 'Company', 
                              'Email': 'Email', 'Profile URL': 'LinkedIn URL', 'Website': 'Website'}
            
            for old_col, new_col in linkedin_columns.items():
                if old_col in linkedin_df.columns:
                    linkedin_df = linkedin_df.rename(columns={old_col: new_col})
        
        # Standardize column names for Apollo data
        if not apollo_df.empty:
            apollo_columns = {'first_name': 'First Name', 'last_name': 'Last Name', 
                             'title': 'Title', 'email': 'Email', 'phone': 'Phone', 'domain': 'Website'}
            
            for old_col, new_col in apollo_columns.items():
                if old_col in apollo_df.columns:
                    apollo_df = apollo_df.rename(columns={old_col: new_col})
            
            # For Apollo, combine first and last name if separate
            if 'First Name' in apollo_df.columns and 'Last Name' in apollo_df.columns:
                apollo_df['Name'] = apollo_df['First Name'] + ' ' + apollo_df['Last Name']
        
        # Combine dataframes
        merged_df = pd.concat([linkedin_df, apollo_df], ignore_index=True)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Save to CSV
        merged_df.to_csv(output_file, index=False)
        logging.info(f"Merged data saved to {output_file} ({len(merged_df)} rows)")
        return output_file
    except Exception as e:
        logging.error(f"Error merging CSV files: {e}")
        return None

def run_full_pipeline():
    """Run the full pipeline with LinkedIn and Apollo in parallel."""
    logging.info("Running full pipeline...")
    
    # Create threads for LinkedIn and Apollo scrapers
    linkedin_thread = threading.Thread(target=lambda: globals().update(linkedin_csv=run_linkedin_scraper()))
    apollo_thread = threading.Thread(target=lambda: globals().update(apollo_csv=run_apollo_scraper()))
    
    # Initialize result variables
    globals()['linkedin_csv'] = None
    globals()['apollo_csv'] = None
    
    # Start both scrapers in parallel
    linkedin_thread.start()
    time.sleep(10)  # Small delay to let LinkedIn initialize first
    apollo_thread.start()
    
    # Wait for both to complete
    linkedin_thread.join()
    apollo_thread.join()
    
    # Get results
    linkedin_csv = globals().get('linkedin_csv')
    apollo_csv = globals().get('apollo_csv')
    
    logging.info(f"LinkedIn scraping completed: {linkedin_csv}")
    logging.info(f"Apollo scraping completed: {apollo_csv}")
    
    # Merge results if at least one was successful
    merged_csv = None
    if linkedin_csv or apollo_csv:
        merged_csv = merge_csv_files(linkedin_csv, apollo_csv)
    else:
        logging.error("Both scrapers failed. No data to process.")
        return
    
    # Process with Snov.io
    if merged_csv:
        processed_csv = run_snovio_email_finder(merged_csv)
        
        # Verify with Hunter.io
        if processed_csv:
            run_hunter_verification(processed_csv)
    else:
        logging.error("Merge failed. Cannot continue pipeline.")

def main():
    """Main entry point with command-line argument support."""
    parser = argparse.ArgumentParser(description="LinkedIn and Apollo Lead Generation Pipeline")
    parser.add_argument("--linkedin-only", action="store_true", help="Run only LinkedIn scraper")
    parser.add_argument("--apollo-only", action="store_true", help="Run only Apollo scraper")
    parser.add_argument("--skip-snovio", action="store_true", help="Skip Snov.io email finding")
    parser.add_argument("--skip-hunter", action="store_true", help="Skip Hunter.io email verification")
    parser.add_argument("--input-csv", help="Use existing CSV file instead of scraping")
    args = parser.parse_args()
    
    try:
        # Create output directory if it doesn't exist
        os.makedirs("output", exist_ok=True)
        os.makedirs("output/screenshots", exist_ok=True)
        
        if args.input_csv:
            # Process existing CSV
            csv_file = args.input_csv
            logging.info(f"Using provided CSV file: {csv_file}")
            
            if not args.skip_snovio:
                csv_file = run_snovio_email_finder(csv_file)
                
            if not args.skip_hunter and csv_file:
                run_hunter_verification(csv_file)
                
        elif args.linkedin_only:
            # Run only LinkedIn scraper
            csv_file = run_linkedin_scraper()
            
            if csv_file and not args.skip_snovio:
                csv_file = run_snovio_email_finder(csv_file)
                
            if csv_file and not args.skip_hunter:
                run_hunter_verification(csv_file)
                
        elif args.apollo_only:
            # Run only Apollo scraper
            csv_file = run_apollo_scraper()
            
            if csv_file and not args.skip_snovio:
                csv_file = run_snovio_email_finder(csv_file)
                
            if csv_file and not args.skip_hunter:
                run_hunter_verification(csv_file)
                
        else:
            # Run full pipeline by default
            run_full_pipeline()
            
    except KeyboardInterrupt:
        logging.warning("Process interrupted by user.")
        
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        
    finally:
        logging.info("Script execution complete.")

if __name__ == "__main__":
    main()