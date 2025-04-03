"""
LinkedIn Sales Navigator Scraper - Main Entry Point
"""
from src.scraper import LinkedInScraper
from src.SalesNav_CSVCleaner import process_csv
from src.ApolloScraper import ApolloScraper
from src.LeadRocksPipeLine import run_leadrocks_scraper
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
from src.utils.file_manager import FileManager
import shutil

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

def run_linkedin_scraper(file_manager):
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
            # Use file manager to get path
            csv_file = file_manager.get_linkedin_path()
            
            # Create DataFrame
            df = pd.DataFrame(leads)
            df.to_csv(str(csv_file), index=False)
            
            logging.info(f"Successfully scraped {len(leads)} leads and saved to {csv_file}")
            
            # Save reference to latest file
            file_manager.save_latest_reference(csv_file, "linkedin")
            
            # Post-process the LinkedIn Sales Navigator CSV
            if csv_file:
                logging.info(f"Post-processing LinkedIn leads with SalesNav_CSVCleaner...")
                output_folder = Path(os.path.dirname(csv_file)) / "processed"
                os.makedirs(output_folder, exist_ok=True)
                
                try:
                    processed_file = file_manager.get_processed_path(source="linkedin")
                    process_csv(csv_file, output_folder)
                    # Use most recent processed file
                    processed_csv = file_manager.get_processed_path(source="linkedin")
                    if processed_csv.exists():
                        logging.info(f"Successfully post-processed LinkedIn leads: {processed_csv}")
                        # Use the processed file for future steps
                        csv_file = processed_csv
                        file_manager.save_latest_reference(csv_file, "linkedin_processed")
                    else:
                        logging.warning("Post-processing completed but couldn't locate the output file")
                except Exception as e:
                    logging.error(f"Error during LinkedIn leads post-processing: {e}")
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

def run_apollo_scraper(file_manager):
    """Run Apollo scraper and return the path to the saved CSV file."""
    logging.info("Running Apollo Scraper...")
    try:
        ApolloScraper()
        
        # Find the Apollo output file - first check for specific naming pattern
        apollo_base_dir = os.path.join(os.path.dirname(file_manager.base_dir), "output")
        apollo_files = [f for f in os.listdir(apollo_base_dir) if f.startswith("ApolloCleaned_Filtered")]
        
        if apollo_files:
            # Sort by modification time (newest first)
            apollo_files.sort(key=lambda x: os.path.getmtime(os.path.join(apollo_base_dir, x)), reverse=True)
            source_file = os.path.join(apollo_base_dir, apollo_files[0])
            
            # Copy to our organized directory
            destination_file = file_manager.get_apollo_path(apollo_files[0])
            shutil.copy2(source_file, destination_file)
            
            logging.info(f"Apollo scraping complete. Results saved to {destination_file}")
            file_manager.save_latest_reference(destination_file, "apollo")
            return destination_file
        else:
            logging.warning("Apollo scraping complete, but couldn't locate the output file.")
            return None
    except Exception as e:
        logging.error(f"An error occurred during Apollo scraping: {e}")
        return None

def run_snovio_email_finder(csv_file, file_manager):
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
            
        # Copy file to processed directory
        output_file = file_manager.get_processed_path(source="snov")
        
        # Make sure directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Copy source file to output location
        shutil.copy2(csv_file, output_file)
        
        # Run the Snov.io email finder directly on the output file
        output_file_str = str(output_file)
        
        # Call the script with the actual file path
        subprocess.run(["python", snov_script_path, "--file", output_file_str], check=False)
        logging.info("Snov.io email finder complete.")
        
        # Save reference to latest file
        file_manager.save_latest_reference(output_file, "snov_processed")
        
        # Run email pattern generation as fallback
        pattern_script_path = os.path.join(script_dir, "src", "email_pattern_generator.py")
        if os.path.exists(pattern_script_path):
            logging.info("Running email pattern generation as fallback...")
            subprocess.run(["python", pattern_script_path, "--file", output_file_str], check=False)
            logging.info("Email pattern generation complete.")
            
        return output_file
    except Exception as e:
        logging.error(f"Error during Snov.io processing: {e}")
        return None

def run_hunter_verification(csv_file, file_manager):
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
        
        # Copy file to processed directory
        output_file = file_manager.get_processed_path(source="hunter")
        
        # Make sure directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Copy source file to output location
        shutil.copy2(csv_file, output_file)
        
        # Convert Path to string
        output_file_str = str(output_file)
            
        # Call the script with the actual file path
        subprocess.run(["python", verifier_script_path, "--file", output_file_str], check=False)
        logging.info("Email verification complete.")
        
        # Save reference to latest file
        file_manager.save_latest_reference(output_file, "verified")
        
        return True
    except Exception as e:
        logging.error(f"Error during Hunter.io verification: {e}")
        return False

def run_full_pipeline():
    """Run the full pipeline with LinkedIn and Apollo in parallel."""
    logging.info("Running full pipeline...")
    
    # Initialize file manager
    file_manager = FileManager()
    
    # Create threads for LinkedIn and Apollo scrapers
    linkedin_thread = threading.Thread(
        target=lambda: globals().update(linkedin_csv=run_linkedin_scraper(file_manager))
    )
    apollo_thread = threading.Thread(
        target=lambda: globals().update(apollo_csv=run_apollo_scraper(file_manager))
    )
    leadrocks_thread = threading.Thread(
        target=lambda: globals().update(leadrocks_csv=run_leadrocks_scraper(file_manager))
    )
    
    # Initialize result variables
    globals()['linkedin_csv'] = None
    globals()['apollo_csv'] = None
    globals()['leadrocks_csv'] = None
    
    # Start scrapers in parallel
    linkedin_thread.start()
    time.sleep(10)  # Small delay to let LinkedIn initialize first
    apollo_thread.start()
    time.sleep(5)  # Small delay before starting LeadRocks
    leadrocks_thread.start()
    
    # Wait for all to complete
    linkedin_thread.join()
    apollo_thread.join()
    leadrocks_thread.join()
    
    # Get results
    linkedin_csv = globals().get('linkedin_csv')
    apollo_csv = globals().get('apollo_csv')
    leadrocks_csv = globals().get('leadrocks_csv')
    
    logging.info(f"LinkedIn scraping completed: {linkedin_csv}")
    logging.info(f"Apollo scraping completed: {apollo_csv}")
    logging.info(f"LeadRocks scraping completed: {leadrocks_csv}")
    
    # Merge results if at least one was successful
    merged_csv = None
    if linkedin_csv or apollo_csv or leadrocks_csv:
        merged_path = file_manager.get_merged_path()
        merged_csv = merge_csv_files(linkedin_csv, apollo_csv, leadrocks_csv, output_file=str(merged_path))
        if merged_csv:
            file_manager.save_latest_reference(merged_csv, "merged")
    else:
        logging.error("All scrapers failed. No data to process.")
        return
    
    # Process with Snov.io
    if merged_csv:
        processed_csv = run_snovio_email_finder(merged_csv, file_manager)
        
        # Verify with Hunter.io
        if processed_csv:
            run_hunter_verification(processed_csv, file_manager)
    else:
        logging.error("Merge failed. Cannot continue pipeline.")

def merge_csv_files(linkedin_csv, apollo_csv, leadrocks_csv=None, output_file="output/merged_leads.csv"):
    """Merge LinkedIn, Apollo and LeadRocks CSV files with proper column standardization."""
    # Initialize with empty DataFrames
    linkedin_df = pd.DataFrame()
    apollo_df = pd.DataFrame()
    leadrocks_df = pd.DataFrame()
    
    # Standard column mapping for all sources
    standard_columns = {
        'first_name': 'first_name',
        'last_name': 'last_name',
        'Role': 'role',
        'Emails': 'email',
        'Email': 'email',
        'Domain': 'domain',
        'Company': 'company',
        'Phone': 'phone',
        'Website': 'website',
        'Misc': 'misc',
        'Profile URL': 'linkedin_url',
        'Title': 'role',  # Map Title to role for consistency
        'Job Title': 'role',  # Map Job Title to role for consistency
        'First Name': 'first_name',  # LeadRocks specific
        'Last Name': 'last_name',  # LeadRocks specific
        'Team Size': 'team_size'  # LeadRocks specific
    }
    
    # Read LinkedIn CSV if available
    if linkedin_csv and os.path.exists(linkedin_csv):
        try:
            linkedin_df = pd.read_csv(linkedin_csv)
            
            # If Name column exists but first_name/last_name don't, split it
            if 'Name' in linkedin_df.columns and 'first_name' not in linkedin_df.columns:
                # Split Name into first and last name
                linkedin_df[['first_name', 'last_name']] = linkedin_df['Name'].str.split(' ', n=1, expand=True)
            
            # Rename columns to standard names
            for old_col, new_col in standard_columns.items():
                if old_col in linkedin_df.columns:
                    linkedin_df = linkedin_df.rename(columns={old_col: new_col})
            
            linkedin_df['source'] = 'LinkedIn'
            logging.info(f"Read {len(linkedin_df)} rows from LinkedIn CSV")
        except Exception as e:
            logging.error(f"Error reading LinkedIn CSV: {e}")
    
    # Read Apollo CSV if available
    if apollo_csv and os.path.exists(apollo_csv):
        try:
            apollo_df = pd.read_csv(apollo_csv)
            
            # Rename columns to standard names
            for old_col, new_col in standard_columns.items():
                if old_col in apollo_df.columns:
                    apollo_df = apollo_df.rename(columns={old_col: new_col})
            
            apollo_df['source'] = 'Apollo'
            logging.info(f"Read {len(apollo_df)} rows from Apollo CSV")
        except Exception as e:
            logging.error(f"Error reading Apollo CSV: {e}")
    
    # Read LeadRocks CSV if available
    if leadrocks_csv and os.path.exists(leadrocks_csv):
        try:
            leadrocks_df = pd.read_csv(leadrocks_csv)
            
            # Rename columns to standard names
            for old_col, new_col in standard_columns.items():
                if old_col in leadrocks_df.columns:
                    leadrocks_df = leadrocks_df.rename(columns={old_col: new_col})
            
            leadrocks_df['source'] = 'LeadRocks'
            logging.info(f"Read {len(leadrocks_df)} rows from LeadRocks CSV")
        except Exception as e:
            logging.error(f"Error reading LeadRocks CSV: {e}")
    
    # If all files are empty/unavailable, return None
    if linkedin_df.empty and apollo_df.empty and leadrocks_df.empty:
        logging.warning("All CSV files are empty or couldn't be read. Cannot merge.")
        return None
    
    try:
        # Combine dataframes
        # First, ensure all have same columns for clean concat
        all_columns = set(list(linkedin_df.columns) + list(apollo_df.columns) + list(leadrocks_df.columns))
        
        # Add missing columns with None values
        for col in all_columns:
            if col not in linkedin_df.columns:
                linkedin_df[col] = None
            if col not in apollo_df.columns:
                apollo_df[col] = None
            if col not in leadrocks_df.columns:
                leadrocks_df[col] = None
        
        # Ensure critical columns exist
        required_columns = ['first_name', 'last_name', 'email', 'company', 'role']
        for col in required_columns:
            if col not in all_columns:
                logging.warning(f"Missing required column '{col}' - adding empty column")
                linkedin_df[col] = None
                apollo_df[col] = None
                leadrocks_df[col] = None
        
        # Convert columns to appropriate types
        for df in [linkedin_df, apollo_df, leadrocks_df]:
            for col in df.columns:
                # Convert to string to avoid type errors, except for boolean columns
                if col != 'Email_Verified':
                    df[col] = df[col].astype(str).replace({'nan': '', 'None': '', 'NaN': ''})
        
        # Combine dataframes
        merged_df = pd.concat([linkedin_df, apollo_df, leadrocks_df], ignore_index=True)
        
        # Clean and standardize emails
        merged_df['email'] = merged_df['email'].astype(str)
        # Remove "+1" or other suffixes from emails
        merged_df['email'] = merged_df['email'].str.replace(r'\+\d+$', '', regex=True)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Select only the key columns for cleaner output
        final_columns = [
            'first_name', 'last_name', 'role', 'company', 'email', 
            'phone', 'website', 'domain', 'linkedin_url', 'source',
            'team_size'  # Added team_size from LeadRocks
        ]
        
        # Only keep columns that exist in our data
        output_columns = [col for col in final_columns if col in merged_df.columns]
        
        # Save to CSV
        merged_df[output_columns].to_csv(output_file, index=False)
        logging.info(f"Merged data saved to {output_file} ({len(merged_df)} rows)")
        return output_file
    except Exception as e:
        logging.error(f"Error merging CSV files: {e}")
        return None

def main():
    """Main entry point with command-line argument support."""
    parser = argparse.ArgumentParser(description="LinkedIn and Apollo Lead Generation Pipeline")
    parser.add_argument("--linkedin-only", action="store_true", help="Run only LinkedIn scraper")
    parser.add_argument("--apollo-only", action="store_true", help="Run only Apollo scraper")
    parser.add_argument("--leadrocks-only", action="store_true", help="Run only LeadRocks scraper")
    parser.add_argument("--skip-snovio", action="store_true", help="Skip Snov.io email finding")
    parser.add_argument("--skip-hunter", action="store_true", help="Skip Hunter.io email verification")
    parser.add_argument("--input-csv", help="Use existing CSV file instead of scraping")
    parser.add_argument("--search-query", help="Search query for LeadRocks (e.g., 'real estate ceo United States')")
    parser.add_argument("--validate-phones", action="store_true", help="Validate phone numbers using ClearoutPhone API")
    args = parser.parse_args()
    
    try:
        # Create output directory if it doesn't exist
        os.makedirs("output", exist_ok=True)
        os.makedirs("output/screenshots", exist_ok=True)
        
        # Initialize file manager
        file_manager = FileManager()
        
        if args.input_csv:
            # Process existing CSV
            csv_file = args.input_csv
            logging.info(f"Using provided CSV file: {csv_file}")
            
            if not args.skip_snovio:
                csv_file = run_snovio_email_finder(csv_file, file_manager)
                
            if not args.skip_hunter and csv_file:
                run_hunter_verification(csv_file, file_manager)
                
        elif args.linkedin_only:
            # Run only LinkedIn scraper
            csv_file = run_linkedin_scraper(file_manager)
            
            if csv_file and not args.skip_snovio:
                csv_file = run_snovio_email_finder(csv_file, file_manager)
                
            if csv_file and not args.skip_hunter:
                run_hunter_verification(csv_file, file_manager)
                
        elif args.apollo_only:
            # Run only Apollo scraper
            csv_file = run_apollo_scraper(file_manager)
            
            if csv_file and not args.skip_snovio:
                csv_file = run_snovio_email_finder(csv_file, file_manager)
                
            if csv_file and not args.skip_hunter:
                run_hunter_verification(csv_file, file_manager)
                
        elif args.leadrocks_only:
            # Run only LeadRocks scraper
            csv_file = run_leadrocks_scraper(file_manager, args.search_query, validate_phones=args.validate_phones)
            
            if csv_file and not args.skip_snovio:
                csv_file = run_snovio_email_finder(csv_file, file_manager)
                
            if csv_file and not args.skip_hunter:
                run_hunter_verification(csv_file, file_manager)
                
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