"""
LeadRocks Pipeline - Automated LinkedIn lead generation and enrichment
"""
import time
import os
import subprocess
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import glob
import pandas as pd
from selenium.webdriver.common.action_chains import ActionChains
import requests
import logging

class LeadRocksScraper:
    """LeadRocks scraper for LinkedIn lead generation and enrichment"""
    
    def __init__(self, file_manager=None):
        self.file_manager = file_manager
        self.driver = None
    
    def get_main_chrome_profile(self):
        """Get the default Chrome profile path for the current user"""
        username = os.environ.get('USERNAME')
        return f"C:\\Users\\{username}\\AppData\\Local\\Google\\Chrome\\User Data"

    def get_most_recent_csv(self):
        """Get the most recent CSV file in the Downloads folder"""
        username = os.environ.get('USERNAME')
        downloads_path = f"C:\\Users\\{username}\\Downloads"
        csv_files = glob.glob(os.path.join(downloads_path, "*.csv"))
        if not csv_files:
            return None
        return max(csv_files, key=os.path.getctime)

    def start_chrome_with_debugging(self, user_profile_path):
        """Start Chrome with remote debugging enabled using the user's existing profile"""
        try:
            chrome_path = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
            if not os.path.exists(chrome_path):
                chrome_path = "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"
            
            cmd = [
                chrome_path,
                f"--user-data-dir={user_profile_path}",
                "--profile-directory=Default",
                "--remote-debugging-port=9222"
            ]
            
            subprocess.Popen(cmd)
            logging.info("Started Chrome with debugging enabled")
            time.sleep(5)
        except Exception as e:
            logging.error(f"Failed to start Chrome: {str(e)}")

    def process_final_csv(self):
        """Process the final downloaded CSV to filter columns"""
        try:
            file_path = self.get_most_recent_csv()
            if not file_path:
                logging.error("No CSV file found to process")
                return None
                
            logging.info(f"Processing CSV file: {file_path}")
            
            # First process the CSV normally
            df = pd.read_csv(file_path)
            
            # Handle both possible column name formats
            name_columns = {
                'First Name': 'First Name',
                'Last Name': 'Last Name',
                'Job Title': 'Job Title',
                'Team Size': 'Team Size'
            }
            
            # Rename columns if needed
            for new_col, old_col in name_columns.items():
                if old_col in df.columns:
                    df = df.rename(columns={old_col: new_col})
                elif new_col not in df.columns:
                    logging.warning(f"Column {new_col}/{old_col} not found in CSV")
            
            # Keep only Phone #1
            phone_columns = [col for col in df.columns if 'Phone #1' in col or 'Phone#1' in col]
            if not phone_columns and 'Phone #1' not in df.columns:
                logging.warning("Phone #1 column not found in CSV")
            
            # Filter out managing directors
            df = df[~df['Job Title'].str.lower().str.contains('managing director', na=False)]
            
            # Keep only desired columns
            columns_to_keep = list(name_columns.keys()) + phone_columns
            
            # Keep only columns that exist
            existing_columns = [col for col in columns_to_keep if col in df.columns]
            df = df[existing_columns]
            
            if self.file_manager:
                output_path = self.file_manager.get_processed_path(source="leadrocks")
            else:
                output_path = file_path.replace('.csv', '_processed.csv')
                
            df.to_csv(output_path, index=False)
            logging.info(f"Processed file saved to: {output_path}")
            logging.info(f"Final row count: {len(df)}")
            logging.info(f"Columns kept: {existing_columns}")
            
            return output_path
            
        except Exception as e:
            logging.error(f"Failed to process CSV: {str(e)}")
            import traceback
            logging.error(traceback.format_exc())
            return None

    def auto_export_leads(self, search_query=None):
        """Connect to Chrome and automatically search and export leads"""
        try:
            options = webdriver.ChromeOptions()
            options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
            self.driver = webdriver.Chrome(options=options)
            logging.info("Connected to Chrome browser")
            
            if not search_query:
                search_query = input("Enter search query (e.g., 'real estate ceo United States'): ")
            search_terms = search_query.split()
            
            if len(search_terms) < 3:
                logging.error("Please enter at least 3 terms: [keywords] [title] [location]")
                return None
            
            location = search_terms[-1]
            if location not in ["US", "United States", "UK", "United Kingdom"]:
                logging.error("Error: Location must be US or UK")
                return None
                
            title = search_terms[-2]
            keywords = " ".join(search_terms[:-2])
            
            geo_urn = "103644278" if location in ["US", "United States"] else "101165590"
            
            url = f"https://www.linkedin.com/search/results/people/?keywords={keywords.replace(' ', '+')}" + \
                f"&origin=FACETED_SEARCH&profileLanguage=%5Ben%5D" + \
                f"&titleFreeText={title}" + \
                f"&industry=%5B44%5D" + \
                f"&geoUrn=%5B{geo_urn}%5D" + \
                f"&serviceCategory=%5B123%5D"
            
            logging.info("Navigating to LinkedIn search...")
            self.driver.get(url)
            wait = WebDriverWait(self.driver, 30)
            
            # Wait for page and extension to load
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "search-results-container")))
            time.sleep(10)  # Give more time for extension to load
            
            logging.info("Looking for export button...")
            # Try to find the "Export profiles to CSV" button
            found_button = False
            try:
                export_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Export profiles to CSV')]")
                logging.info("Found button using XPath")
                found_button = True
            except:
                logging.info("Button not found with XPath, trying other methods...")
                
                # Second method: Look through all buttons
                all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
                logging.info(f"Found {len(all_buttons)} buttons on page")
                
                for button in all_buttons:
                    try:
                        if "Export profiles to CSV" in button.text:
                            export_button = button
                            logging.info("Found button by scanning text")
                            found_button = True
                            break
                    except:
                        continue
            
            # Click the button if found
            if found_button:
                logging.info("Attempting to click the export button...")
                try:
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", export_button)
                    time.sleep(2)
                    self.driver.execute_script("arguments[0].click();", export_button)
                    logging.info("Clicked export button")
                    
                    # Wait for the number input field and set value
                    time.sleep(3)  # Wait for dialog to appear
                    logging.info("Setting number of profiles...")
                    input_field = self.driver.find_element(By.XPATH, "//input[@type='number']")
                    self.driver.execute_script("arguments[0].value = '';", input_field)  # Clear using JavaScript
                    input_field.send_keys("10")  # Set to 1000 as shown in image
                    
                    # Click the Export CSV button in dialog
                    logging.info("Clicking Export CSV button...")
                    export_csv_button = self.driver.find_element(By.XPATH, "//button[text()='Export CSV']")
                    self.driver.execute_script("arguments[0].click();", export_csv_button)
                    logging.info("Started export process")
                    
                    # Wait for Save CSV button to appear and be clicked
                    logging.info("Waiting for export to complete and Save CSV button to appear...")
                    start_time = time.time()
                    save_csv_clicked = False
                    
                    while time.time() - start_time < 300:  # 5 minute timeout
                        try:
                            # Look for Save CSV button
                            save_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Save CSV')]")
                            for save_btn in save_buttons:
                                if save_btn.is_displayed():
                                    logging.info("Found Save CSV button, attempting to click...")
                                    self.driver.execute_script("arguments[0].click();", save_btn)
                                    save_csv_clicked = True
                                    logging.info("Clicked Save CSV button")
                                    time.sleep(5)  # Wait for download to start
                                    break
                            
                            if save_csv_clicked:
                                break
                                
                        except Exception as e:
                            pass  # Continue waiting if button not found
                            
                        logging.info("Still waiting for Save CSV button...")
                        time.sleep(10)  # Check every 10 seconds
                    
                    if not save_csv_clicked:
                        logging.error("Timed out waiting for Save CSV button")
                        return None
                    
                    logging.info("Export completed and saved. Proceeding to enrichment...")
                    time.sleep(5)  # Give time for download to complete
                    
                except Exception as e:
                    logging.error(f"Failed to interact with export dialog: {str(e)}")
                    return None
                        
            if not found_button:
                logging.error("Could not find the 'Export profiles to CSV' button")
                return None
            
            logging.info("Waiting for download...")
            time.sleep(5)
            file_path = self.get_most_recent_csv()
            
            logging.info("Navigating to LeadRocks enrichment...")
            self.driver.get("https://leadrocks.io/my/enrich")
            time.sleep(5)
            
            logging.info("Uploading CSV file...")
            file_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='file']")))
            file_input.send_keys(file_path)
            
            logging.info("Starting enrichment...")
            start_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Start enrichment')]")))
            self.driver.execute_script("arguments[0].click();", start_btn)
            time.sleep(2)
            
            logging.info("Setting list name...")
            text_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='text']")))
            text_input.send_keys("automated list")
            
            logging.info("Saving list...")
            save_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Save to list')]")))
            self.driver.execute_script("arguments[0].click();", save_btn)
            time.sleep(5)
            
            logging.info("Selecting all leads...")
            select_all = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@data-action='check-all']")))
            self.driver.execute_script("arguments[0].click();", select_all)
            time.sleep(2)
            
            logging.info("Exporting enriched data...")
            try:
                export_link = wait.until(EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/my/leads') and contains(@href, 'csv=1')]")))
                self.driver.execute_script("arguments[0].click();", export_link)
            except:
                export_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Export list to CSV')]")))
                self.driver.execute_script("arguments[0].click();", export_btn)
            
            logging.info("Waiting for final export...")
            time.sleep(5)
            return self.process_final_csv()
            
        except Exception as e:
            logging.error(f"Error: {str(e)}")
            return None
        finally:
            if self.driver:
                self.driver.quit()

def run_leadrocks_scraper(file_manager=None, search_query=None):
    """Run LeadRocks scraper and return the path to the saved CSV file."""
    logging.info("Starting LeadRocks Scraper...")
    
    try:
        options = webdriver.ChromeOptions()
        options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        driver = webdriver.Chrome(options=options)
        logging.info("Connected to existing Chrome browser")
        driver.quit()
    except:
        logging.info("No debugging-enabled Chrome found. Starting new instance...")
        user_profile = LeadRocksScraper().get_main_chrome_profile()
        LeadRocksScraper().start_chrome_with_debugging(user_profile)
        time.sleep(5)
    
    scraper = LeadRocksScraper(file_manager)
    csv_file = scraper.auto_export_leads(search_query)
    
    if csv_file:
        logging.info("LeadRocks scraping complete.")
        if file_manager:
            file_manager.save_latest_reference(csv_file, "leadrocks")
    else:
        logging.error("LeadRocks scraping failed.")
    
    return csv_file