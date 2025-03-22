"""
Lead Generation Tool - Main Entry Point
"""
from src.scraper import LinkedInScraper
import logging
import sys
import time
import os
import subprocess
import glob

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

def get_latest_csv_file(directory="output"):
    """
    Get the latest CSV file from the specified directory.
    
    Args:
        directory (str): Path to the directory containing CSV files.
        
    Returns:
        str: Path to the latest CSV file.
    """
    list_of_files = glob.glob(os.path.join(directory, '*.csv'))
    if not list_of_files:
        raise FileNotFoundError(f"No CSV files found in the {directory} directory")
    latest_file = max(list_of_files, key=os.path.getctime)
    return latest_file

def run_linkedin_scraper():
    """Run LinkedIn Sales Navigator scraper and return the path to the saved CSV file."""
    print("[INFO] Starting LinkedIn Sales Navigator Scraper...")
    scraper = None
    csv_file = None
    
    try:
        # Initialize and login
        scraper = LinkedInScraper()
        scraper.login()
        
        # Extract profile links
        print("[INFO] Extracting profile links from search results...")
        profile_links = scraper.get_profile_links()
        
        if len(profile_links) == 0:
            print("[ERROR] No profile links found. Exiting.")
            return None
            
        # Scrape individual profiles
        print(f"[INFO] Scraping {len(profile_links)} profiles...")
        leads = scraper.scrape_profiles(profile_links)
        
        # Save results to CSV
        if leads:
            scraper.save_to_csv(leads)
            # Fix: If save_to_csv returns None but printed a file path, try to find the file
            try:
                # Try to get the latest CSV file from the output directory
                csv_file = get_latest_csv_file()
                print(f"[INFO] Using latest CSV file: {csv_file}")
            except FileNotFoundError:
                print("[ERROR] Could not locate the saved CSV file.")
            
            print(f"[OK] Successfully scraped {len(leads)} leads and saved to {csv_file}")
        else:
            print("[ERROR] No leads were collected.")
    
    except KeyboardInterrupt:
        print("[WARNING] Process interrupted by user.")
    
    except Exception as e:
        print(f"[ERROR] An error occurred: {e}")
    
    finally:
        # Clean up
        if scraper:
            scraper.cleanup()
        print("[INFO] LinkedIn scraping complete.")
    
    return csv_file

def run_facebook_scraper():
    """Run Facebook scraper and return the path to the saved CSV file."""
    try:
        # Import the Facebook scraper here to avoid circular imports
        from facebook.scraper import FacebookScraper
        
        print("[INFO] Starting Facebook Scraper...")
        
        # Initialize the scraper
        scraper = FacebookScraper()
        
        # Run the scraper
        csv_file = scraper.run()
        
        if csv_file:
            print(f"[OK] Successfully scraped Facebook leads and saved to {csv_file}")
        else:
            print("[WARNING] No leads collected from Facebook.")
        
        return csv_file
    
    except Exception as e:
        print(f"[ERROR] An error occurred during Facebook scraping: {e}")
        return None

def run_snovio_email_finder(csv_file=None):
    """Run Snov.io email finder on a CSV file."""
    if csv_file is None:
        try:
            csv_file = get_latest_csv_file()
            print(f"[INFO] Using latest CSV file: {csv_file}")
        except FileNotFoundError as e:
            print(f"[ERROR] {str(e)}")
            return None
    
    print("[INFO] Running Snov.io email finder...")
    try:
        # Fix: Use the correct path to snov_email_finder.py
        # First try in src/utils, then fallback to src
        snov_script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src", "utils", "snov_email_finder.py")
        if not os.path.exists(snov_script_path):
            snov_script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src", "snov_email_finder.py")
        
        csv_filename = os.path.basename(csv_file) if csv_file else None
        if csv_filename:
            subprocess.run(["python", snov_script_path, "--file", csv_filename], check=True)
            print("[OK] Snov.io email finder complete.")
            
            # New: Run email pattern generation as fallback for missing emails
            print("[INFO] Running email pattern generation as fallback for missing emails...")
            try:
                pattern_script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src", "email_pattern_generator.py")
                if os.path.exists(pattern_script_path):
                    subprocess.run(["python", pattern_script_path, "--file", csv_filename], check=True)
                    print("[OK] Email pattern generation complete.")
                else:
                    print("[WARNING] Email pattern generator script not found.")
            except Exception as e:
                print(f"[WARNING] Email pattern generation failed: {e}")
            
            return csv_file
        else:
            print("[WARNING] No CSV filename available for Snov.io processing")
            return None
    except Exception as e:
        print(f"[ERROR] Snov.io email finder failed: {e}")
        return None

def run_hunter_verification(csv_file=None):
    """Run Hunter.io email verification on a CSV file."""
    if csv_file is None:
        try:
            csv_file = get_latest_csv_file()
            print(f"[INFO] Using latest CSV file: {csv_file}")
        except FileNotFoundError as e:
            print(f"[ERROR] {str(e)}")
            return None
    
    print("[INFO] Verifying emails with Hunter.io...")
    try:
        # Fix: Use the correct path to email_verifier.py
        # First try in src/utils, then fallback to src
        verifier_script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src", "utils", "email_verifier.py")
        if not os.path.exists(verifier_script_path):
            verifier_script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src", "email_verifier.py")
        
        csv_filename = os.path.basename(csv_file) if csv_file else None
        if csv_filename:
            subprocess.run(["python", verifier_script_path, "--file", csv_filename], check=True)
            print("[OK] Email verification complete.")
            return True
        else:
            print("[WARNING] No CSV filename available for email verification")
            return False
    except Exception as e:
        print(f"[ERROR] Email verification failed: {e}")
        return False

def display_menu():
    """Display the main menu and return user choice."""
    print("\n" + "="*50)
    print("Lead Generation Automation Tool")
    print("="*50)
    print("1. Run LinkedIn Sales Navigator Scraper")
    print("2. Run Facebook Group/Page Scraper")
    print("3. Run Snov.io Email Finder (on latest CSV)")
    print("4. Run Hunter.io Email Verification (on latest CSV)")
    print("5. Run Full LinkedIn Pipeline (LinkedIn → Snov.io → Hunter.io)")
    print("6. Run Full Facebook Pipeline (Facebook → Snov.io → Hunter.io)")
    print("0. Exit")
    print("="*50)
    
    while True:
        try:
            choice = int(input("Enter your choice [0-6]: "))
            if 0 <= choice <= 6:
                return choice
            else:
                print("Invalid choice. Please enter a number between 0 and 6.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def get_yes_no_input(prompt):
    """Get yes/no input from user."""
    while True:
        response = input(f"{prompt} (y/n): ").lower().strip()
        if response in ["y", "yes"]:
            return True
        elif response in ["n", "no"]:
            return False
        else:
            print("Please answer 'y' or 'n'.")

def main():
    """Main entry point for the Lead Generation automation tool."""
    try:
        while True:
            choice = display_menu()
            
            if choice == 0:  # Exit
                print("[INFO] Exiting program. Goodbye!")
                break
                
            elif choice == 1:  # LinkedIn Scraper
                csv_file = run_linkedin_scraper()
                if csv_file and get_yes_no_input("Would you like to run Snov.io Email Finder on this data?"):
                    csv_file = run_snovio_email_finder(csv_file)  # Update csv_file with result
                    if csv_file and get_yes_no_input("Would you like to verify the emails with Hunter.io?"):
                        run_hunter_verification(csv_file)
                
            elif choice == 2:  # Facebook Scraper
                csv_file = run_facebook_scraper()
                if csv_file and get_yes_no_input("Would you like to run Snov.io Email Finder on this data?"):
                    csv_file = run_snovio_email_finder(csv_file)  # Update csv_file with result
                    if csv_file and get_yes_no_input("Would you like to verify the emails with Hunter.io?"):
                        run_hunter_verification(csv_file)
                
            elif choice == 3:  # Snov.io Email Finder
                csv_file = run_snovio_email_finder()
                if csv_file and get_yes_no_input("Would you like to verify the emails with Hunter.io?"):
                    run_hunter_verification(csv_file)
                
            elif choice == 4:  # Hunter.io Email Verification
                run_hunter_verification()
                
            elif choice == 5:  # Full LinkedIn Pipeline
                print("[INFO] Running full LinkedIn pipeline...")
                csv_file = run_linkedin_scraper()
                if csv_file:
                    csv_file = run_snovio_email_finder(csv_file)  # Now includes pattern fallback
                    if csv_file:  # Only proceed if email finding was successful
                        run_hunter_verification(csv_file)
                    else:
                        print("[WARNING] Skipping Hunter.io verification due to email finder failure")
            
            elif choice == 6:  # Full Facebook Pipeline
                print("[INFO] Running full Facebook pipeline...")
                csv_file = run_facebook_scraper()
                if csv_file:
                    csv_file = run_snovio_email_finder(csv_file)  # Now includes pattern fallback
                    if csv_file:  # Only proceed if email finding was successful
                        run_hunter_verification(csv_file)
                    else:
                        print("[WARNING] Skipping Hunter.io verification due to email finder failure")
            
            if choice != 0 and not get_yes_no_input("Would you like to return to the main menu?"):
                print("[INFO] Exiting program. Goodbye!")
                break
                
    except KeyboardInterrupt:
        print("\n[WARNING] Process interrupted by user.")
    
    except Exception as e:
        print(f"\n[ERROR] An unexpected error occurred: {e}")
    
    finally:
        print("[INFO] Script execution complete.")

if __name__ == "__main__":
    main()