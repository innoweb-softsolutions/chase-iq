"""
LinkedIn Sales Navigator Scraper - Main Entry Point
"""
from src.scraper import LinkedInScraper
import logging
import sys
import time
import os
import subprocess

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

def main():
    """Main entry point for the LinkedIn Sales Navigator scraper."""
    print("[INFO] Starting LinkedIn Sales Navigator Scraper...")
    scraper = None
    
    try:
        # Initialize and login
        scraper = LinkedInScraper()
        scraper.login()
        
        # Extract profile links
        print("[INFO] Extracting profile links from search results...")
        profile_links = scraper.get_profile_links()
        
        if len(profile_links) == 0:
            print("[ERROR] No profile links found. Exiting.")
            return
            
        # Scrape individual profiles
        print(f"[INFO] Scraping {len(profile_links)} profiles...")
        leads = scraper.scrape_profiles(profile_links)
        
        # Save results to CSV
        csv_file = None
        if leads:
            csv_file = scraper.save_to_csv(leads)
            print(f"[OK] Successfully scraped {len(leads)} leads.")

            # Step 2: Run Snov.io email finder for missing emails
            print("[INFO] Step 2: Running Snov.io email finder for missing emails...")
            try:
                snov_script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src", "snov_email_finder.py")
                csv_filename = os.path.basename(csv_file) if csv_file else None
                if csv_filename:
                    subprocess.run(["python", snov_script_path, "--file", csv_filename], check=True)
                    print("[OK] Snov.io email finder complete.")
                else:
                    print("[WARNING] No CSV filename available for Snov.io processing")
            except Exception as e:
                print(f"[WARNING] Snov.io email finder failed: {e}")
            
            # Step 3: Run pattern generation for still-missing emails
            print("[INFO] Step 3: Generating email patterns for missing emails...")
            try:
                pattern_script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src", "email_pattern_generator.py")
                csv_filename = os.path.basename(csv_file) if csv_file else None
                if csv_filename:
                    subprocess.run(["python", pattern_script_path, "--file", csv_filename], check=True)
                    print("[OK] Email pattern generation complete.")
                else:
                    print("[WARNING] No CSV filename available for pattern generation")
            except Exception as e:
                print(f"[WARNING] Email pattern generation failed: {e}")
                
            # Step 4: Run email verification on the file
            print("[INFO] Step 4: Verifying all emails with Hunter.io...")
            try:
                verifier_script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src", "email_verifier.py")
                csv_filename = os.path.basename(csv_file) if csv_file else None
                if csv_filename:
                    subprocess.run(["python", verifier_script_path, "--file", csv_filename], check=True)
                    print("[OK] Email verification complete.")
                else:
                    print("[WARNING] No CSV filename available for email verification")
            except Exception as e:
                print(f"[WARNING] Email verification failed: {e}")
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
        print("[INFO] Script execution complete.")

if __name__ == "__main__":
    main()