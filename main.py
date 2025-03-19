"""
LinkedIn Sales Navigator Scraper - Main Entry Point
"""
from src.scraper import LinkedInScraper
import logging
import sys
import time
import os

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
        if leads:
            scraper.save_to_csv(leads)
            print(f"[OK] Successfully scraped {len(leads)} leads.")
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
