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
from datetime import datetime

class LeadRocksScraper:
    """LeadRocks scraper for LinkedIn lead generation and enrichment"""
    
    def __init__(self, file_manager=None):
        self.file_manager = file_manager
        self.driver = None
        self.output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output')
        self.current_run = None
        self.setup_output_dirs()
    
    def setup_output_dirs(self):
        """Setup output directory structure for current run"""
        # Create timestamp for current run
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.current_run = f"run_{timestamp}"
        
        # Create directory structure
        run_dir = os.path.join(self.output_dir, self.current_run)
        subdirs = ['processed', 'screenshots', 'apollo', 'leadrocks', 'linkedin', 'merged']
        
        for subdir in subdirs:
            os.makedirs(os.path.join(run_dir, subdir), exist_ok=True)
        
        logging.info(f"Created output directory structure in {run_dir}")
        return run_dir

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
            
            # Define all possible column variations
            column_mapping = {
                'First Name': ['First Name', 'FirstName', 'First_Name'],
                'Last Name': ['Last Name', 'LastName', 'Last_Name'],
                'Job Title': ['Job Title', 'JobTitle', 'Title', 'Position'],
                'Team Size': ['Team Size', 'TeamSize', 'Company Size', 'CompanySize'],
                'Company': ['Company', 'Company Name', 'CompanyName'],
                'Industry': ['Industry', 'Industry Type'],
                'Phone': ['Phone #1', 'Phone#1', 'Phone', 'PhoneNumber'],
                'Email': ['Email', 'Work Email', 'WorkEmail', 'Business Email']
            }
            
            # Create a new DataFrame with standardized columns
            new_df = pd.DataFrame()
            
            # Map and copy data for each column
            for new_col, possible_names in column_mapping.items():
                existing_col = next((col for col in possible_names if col in df.columns), None)
                if existing_col:
                    new_df[new_col] = df[existing_col]
                else:
                    new_df[new_col] = ''
                    logging.warning(f"Column {new_col} not found in original CSV")
            
            # Clean up phone numbers
            if 'Phone' in new_df.columns:
                new_df['Phone'] = new_df['Phone'].astype(str).replace({'nan': '', 'None': '', 'unknown': ''})
                new_df['Phone'] = new_df['Phone'].apply(lambda x: ''.join(c for c in str(x) if c.isdigit() or c == '+'))
            
            # Clean up email addresses
            if 'Email' in new_df.columns:
                new_df['Email'] = new_df['Email'].astype(str).replace({'nan': '', 'None': '', 'unknown': ''})
                new_df['Email'] = new_df['Email'].str.strip()
            
            # Convert Team Size to numeric
            new_df['Team Size'] = pd.to_numeric(new_df['Team Size'].astype(str).replace({
                'nan': '0', 'None': '0', 'unknown': '0', '': '0'
            }), errors='coerce').fillna(0).astype(int)
            
            # Filter out managing directors
            if 'Job Title' in new_df.columns:
                new_df = new_df[~new_df['Job Title'].str.lower().str.contains('managing director', na=False)]
            
            # Save to the leadrocks directory in current run
            date_str = datetime.now().strftime('%Y_%m_%d')
            filename = f"leadrocks_automated_list_{date_str}_processed.csv"
            
            # Save in the leadrocks subdirectory of current run
            output_path = os.path.join(self.output_dir, self.current_run, 'leadrocks', filename)
            new_df.to_csv(output_path, index=False)
            
            # Also save a copy in processed directory
            processed_path = os.path.join(self.output_dir, self.current_run, 'processed', filename)
            new_df.to_csv(processed_path, index=False)
            
            logging.info(f"Processed file saved to: {output_path}")
            logging.info(f"Backup saved to: {processed_path}")
            logging.info(f"Final row count: {len(new_df)}")
            logging.info(f"Columns in final CSV: {list(new_df.columns)}")
            
            # Call the API validation with the processed file
            self.validate_phone_numbers(processed_path)
            
            return processed_path
            
        except Exception as e:
            logging.error(f"Failed to process CSV: {str(e)}")
            import traceback
            logging.error(traceback.format_exc())
            return None

    def validate_phone_numbers(self, filepath):
        """Validate phone numbers using the ClearoutPhone API"""
        try:
            url = "https://api.clearoutphone.io/v1/phonenumber/bulk"
            api_token = "a04f0ffd1d4c2a7f2f13447e43e0a640:39ec3ccba26b7756b7099333fde72ff88303adbaa8b8950a482ebcb7091a238c"

            with open(filepath, "rb") as file:
                files = {"file": file}
                payload = {"country_code": 'us'}
                headers = {
                    'Authorization': f"Bearer:{api_token}",
                }

                response = requests.request(
                    "POST",
                    url,
                    files=files,
                    verify=False,
                    headers=headers,
                    data=payload
                )

                # Save API response in the processed directory
                response_file = filepath.replace('.csv', '_api_response.json')
                with open(response_file, 'w') as f:
                    f.write(response.text)
                
                logging.info(f"API Response saved to: {response_file}")

                if response.status_code == 200:
                    logging.info("Phone number validation completed successfully!")
                else:
                    logging.error(f"API request failed with status code {response.status_code}")

        except Exception as e:
            logging.error(f"An error occurred during phone validation: {str(e)}")

    def auto_export_leads(self, search_query=None):
        """Connect to Chrome and automatically search and export leads"""
        try:
            options = webdriver.ChromeOptions()
            options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
            self.driver = webdriver.Chrome(options=options)
            logging.info("Connected to Chrome browser")
            
            if not search_query:
                search_query = input("Enter search query (e.g., 'real estate ceo US'): ")
            search_terms = search_query.split()
            
            if len(search_terms) < 3:
                logging.error("Please enter at least 3 terms: [keywords] [title] [location]")
                return None
            
            location = search_terms[-1]
            if location not in ["US", "UK"]:
                logging.error("Error: Location must be US or UK")
                return None
                
            title = search_terms[-2]
            keywords = " ".join(search_terms[:-2])
            
            geo_urn = "103644278" if location == "US" else "101165590"
            
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
                    
                    # Start checking for Continue button in parallel with other operations
                    continue_check_start_time = time.time()
                    
                    # Wait for the number input field and set value
                    time.sleep(3)  # Wait for dialog to appear
                    logging.info("Setting number of profiles...")
                    input_field = self.driver.find_element(By.XPATH, "//input[@type='number']")
                    self.driver.execute_script("arguments[0].value = '';", input_field)  # Clear using JavaScript
                    input_field.send_keys("20")  
                    
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
                            # Check for Continue button first
                            try:
                                continue_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Continue')]")
                                for btn in continue_buttons:
                                    if btn.is_displayed():
                                        logging.info("Found Continue button, clicking...")
                                        self.driver.execute_script("arguments[0].click();", btn)
                            except Exception as e:
                                pass  # Ignore continue button errors
                            
                            # Then check for Save CSV button
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
                        time.sleep(2)  # Check every 2 seconds
                    
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
    
    # Initialize Chrome with debugging
    user_profile = LeadRocksScraper().get_main_chrome_profile()
    
    # Kill any existing Chrome processes
    try:
        import psutil
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] == 'chrome.exe':
                try:
                    proc.kill()
                except:
                    pass
        time.sleep(2)  # Wait for processes to close
    except ImportError:
        logging.warning("psutil not installed, skipping Chrome process cleanup")
    
    # Start Chrome with debugging enabled
    try:
        LeadRocksScraper().start_chrome_with_debugging(user_profile)
        logging.info("Started Chrome with debugging enabled")
        time.sleep(5)  # Wait for Chrome to start
    except Exception as e:
        logging.error(f"Failed to start Chrome: {str(e)}")
        return None
    
    # Create scraper and run
    try:
        scraper = LeadRocksScraper(file_manager)
        csv_file = scraper.auto_export_leads(search_query)
        
        if csv_file:
            logging.info("LeadRocks scraping complete.")
            if file_manager:
                file_manager.save_latest_reference(csv_file, "leadrocks")
        else:
            logging.error("LeadRocks scraping failed.")
        
        return csv_file
    except Exception as e:
        logging.error(f"Error during scraping: {str(e)}")
        return None