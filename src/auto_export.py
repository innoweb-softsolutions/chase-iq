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

def get_main_chrome_profile():
    """Get the default Chrome profile path for the current user"""
    username = os.environ.get('USERNAME')
    return f"C:\\Users\\{username}\\AppData\\Local\\Google\\Chrome\\User Data"

def get_most_recent_csv():
    """Get the most recent CSV file in the Downloads folder"""
    username = os.environ.get('USERNAME')
    downloads_path = f"C:\\Users\\{username}\\Downloads"
    csv_files = glob.glob(os.path.join(downloads_path, "*.csv"))
    if not csv_files:
        return None
    return max(csv_files, key=os.path.getctime)

def start_chrome_with_debugging(user_profile_path):
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
        print("Started Chrome with debugging enabled")
        time.sleep(5)
    except Exception as e:
        print(f"Failed to start Chrome: {str(e)}")

def process_final_csv():
    """Process the final downloaded CSV to filter columns"""
    try:
        file_path = get_most_recent_csv()
        if not file_path:
            print("[ERROR] No CSV file found to process")
            return
            
        print(f"\n[DEBUG] Processing CSV file: {file_path}")
        
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
                print(f"[WARNING] Column {new_col}/{old_col} not found in CSV")
        
        # Keep only Phone #1
        phone_columns = [col for col in df.columns if 'Phone #1' in col or 'Phone#1' in col]
        if not phone_columns and 'Phone #1' not in df.columns:
            print("[WARNING] Phone #1 column not found in CSV")
        
        # Filter out managing directors
        df = df[~df['Job Title'].str.lower().str.contains('managing director', na=False)]
        
        # Keep only desired columns
        columns_to_keep = list(name_columns.keys()) + phone_columns
        
        # Keep only columns that exist
        existing_columns = [col for col in columns_to_keep if col in df.columns]
        df = df[existing_columns]
        
        output_path = file_path.replace('.csv', '_processed.csv')
        df.to_csv(output_path, index=False)
        print(f"[SUCCESS] Processed file saved to: {output_path}")
        print(f"Final row count: {len(df)}")
        print("Columns kept:", existing_columns)
        
    except Exception as e:
        print(f"[ERROR] Failed to process CSV: {str(e)}")
        import traceback
        print(traceback.format_exc())

def auto_export_leads():
    """Connect to Chrome and automatically search and export leads"""
    try:
        options = webdriver.ChromeOptions()
        options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        driver = webdriver.Chrome(options=options)
        print("Connected to Chrome browser")
        
        search_query = input("Enter search query (e.g., 'real estate ceo United States'): ")
        search_terms = search_query.split()
        
        if len(search_terms) < 3:
            print("Please enter at least 3 terms: [keywords] [title] [location]")
            return
        
        location = search_terms[-1]
        if location not in ["US", "United States", "UK", "United Kingdom"]:
            print("Error: Location must be US or UK")
            return
            
        title = search_terms[-2]
        keywords = " ".join(search_terms[:-2])
        
        geo_urn = "103644278" if location in ["US", "United States"] else "101165590"
        
        url = f"https://www.linkedin.com/search/results/people/?keywords={keywords.replace(' ', '+')}" + \
            f"&origin=FACETED_SEARCH&profileLanguage=%5Ben%5D" + \
            f"&titleFreeText={title}" + \
            f"&industry=%5B44%5D" + \
            f"&geoUrn=%5B{geo_urn}%5D" + \
            f"&serviceCategory=%5B123%5D"
        
        print(f"Navigating to LinkedIn search...")
        driver.get(url)
        wait = WebDriverWait(driver, 30)
        
        # Wait for page and extension to load
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "search-results-container")))
        time.sleep(10)  # Give more time for extension to load
        
        print("Looking for export button...")
        # Try to find the "Export profiles to CSV" button
        found_button = False
        try:
            export_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Export profiles to CSV')]")
            print("Found button using XPath")
            found_button = True
        except:
            print("Button not found with XPath, trying other methods...")
            
            # Second method: Look through all buttons
            all_buttons = driver.find_elements(By.TAG_NAME, "button")
            print(f"Found {len(all_buttons)} buttons on page")
            
            for button in all_buttons:
                try:
                    if "Export profiles to CSV" in button.text:
                        export_button = button
                        print("Found button by scanning text")
                        found_button = True
                        break
                except:
                    continue
        
        # Click the button if found
        if found_button:
            print("Attempting to click the export button...")
            try:
                driver.execute_script("arguments[0].scrollIntoView(true);", export_button)
                time.sleep(2)
                driver.execute_script("arguments[0].click();", export_button)
                print("Clicked export button")
                
                # Wait for the number input field and set value
                time.sleep(3)  # Wait for dialog to appear
                print("Setting number of profiles...")
                input_field = driver.find_element(By.XPATH, "//input[@type='number']")
                driver.execute_script("arguments[0].value = '';", input_field)  # Clear using JavaScript
                input_field.send_keys("10")  # Set to 1000 as shown in image
                
                # Click the Export CSV button in dialog
                print("Clicking Export CSV button...")
                export_csv_button = driver.find_element(By.XPATH, "//button[text()='Export CSV']")
                driver.execute_script("arguments[0].click();", export_csv_button)
                print("Started export process")
                
                # Wait for Save CSV button to appear and be clicked
                print("Waiting for export to complete and Save CSV button to appear...")
                start_time = time.time()
                save_csv_clicked = False
                
                while time.time() - start_time < 300:  # 5 minute timeout
                    try:
                        # Look for Save CSV button
                        save_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Save CSV')]")
                        for save_btn in save_buttons:
                            if save_btn.is_displayed():
                                print("Found Save CSV button, attempting to click...")
                                driver.execute_script("arguments[0].click();", save_btn)
                                save_csv_clicked = True
                                print("Clicked Save CSV button")
                                time.sleep(5)  # Wait for download to start
                                break
                        
                        if save_csv_clicked:
                            break
                            
                    except Exception as e:
                        pass  # Continue waiting if button not found
                        
                    print("Still waiting for Save CSV button...")
                    time.sleep(10)  # Check every 10 seconds
                
                if not save_csv_clicked:
                    print("Timed out waiting for Save CSV button")
                    return
                
                print("Export completed and saved. Proceeding to enrichment...")
                time.sleep(5)  # Give time for download to complete
                
            except Exception as e:
                print(f"Failed to interact with export dialog: {str(e)}")
                return
                    
        if not found_button:
            print("Could not find the 'Export profiles to CSV' button")
            return
        
        print("Waiting for download...")
        time.sleep(5)
        file_path = get_most_recent_csv()
        
        print("Navigating to LeadRocks enrichment...")
        driver.get("https://leadrocks.io/my/enrich")
        time.sleep(5)
        
        print("Uploading CSV file...")
        file_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='file']")))
        file_input.send_keys(file_path)
        
        print("Starting enrichment...")
        start_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Start enrichment')]")))
        driver.execute_script("arguments[0].click();", start_btn)
        time.sleep(2)
        
        print("Setting list name...")
        text_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='text']")))
        text_input.send_keys("automated list")
        
        print("Saving list...")
        save_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Save to list')]")))
        driver.execute_script("arguments[0].click();", save_btn)
        time.sleep(5)
        
        print("Selecting all leads...")
        select_all = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@data-action='check-all']")))
        driver.execute_script("arguments[0].click();", select_all)
        time.sleep(2)
        
        print("Exporting enriched data...")
        try:
            export_link = wait.until(EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/my/leads') and contains(@href, 'csv=1')]")))
            driver.execute_script("arguments[0].click();", export_link)
        except:
            export_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Export list to CSV')]")))
            driver.execute_script("arguments[0].click();", export_btn)
        
        print("Waiting for final export...")
        time.sleep(5)
        process_final_csv()
        
    except Exception as e:
        print(f"Error: {str(e)}")

def main():
    print("AutoExport - LinkedIn Lead Generation")
    
    try:
        options = webdriver.ChromeOptions()
        options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        driver = webdriver.Chrome(options=options)
        print("Connected to existing Chrome browser")
    except:
        print("No debugging-enabled Chrome found. Starting new instance...")
        user_profile = get_main_chrome_profile()
        start_chrome_with_debugging(user_profile)
        time.sleep(5)
    
    auto_export_leads()
    print("\nProcess completed.")

if __name__ == "__main__":
    main()