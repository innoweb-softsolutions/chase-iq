from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from .ApolloCSVCleaner import clean_csv, merge_cleaned
import undetected_chromedriver as uc
from distutils.util import strtobool
from dotenv import load_dotenv
from pathlib import Path
import time
import copy
import csv
import os
import re

def login_google(browser, indexedEmail, indexedPassword):
    """Fills in the user details and handles 2-factor authentication"""
    loginID = WebDriverWait(browser, 10).until(
        EC.element_to_be_clickable((By.ID, "identifierId"))
    )
    loginID.send_keys(indexedEmail)
    loginID.send_keys(Keys.ENTER)

    passField = WebDriverWait(browser, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='password']"))
    )
    passField.send_keys(indexedPassword)
    passField.send_keys(Keys.ENTER)
    
    # Wait for potential 2-factor authentication
    print("[INFO] Checking for 2-step verification...")
    time.sleep(5)  # Give the page a moment to transition
    
    # Better detection method using URL patterns and page content
    try:
        # Wait up to 20 seconds to see if we land on a verification page
        for i in range(4):  # Check a few times
            current_url = browser.current_url
            page_source = browser.page_source.lower()
            
            # Check for common verification indicators
            verification_indicators = [
                "challenge" in current_url,
                "signin/v2/challenge" in current_url,
                "2-step verification" in page_source,
                "verification" in page_source and "step" in page_source,
                "open the gmail app" in page_source,
                "google sent a notification" in page_source
            ]
            
            if any(verification_indicators):
                print("[INFO] 2-step verification required. Waiting for manual verification (maximum 3 minutes)...")
                
                # Wait for up to 3 minutes for manual verification
                for i in range(18):  # 18 x 10 seconds = 3 minutes
                    print(f"[INFO] Waiting for verification... ({i+1}/18)")
                    # Check if we've moved past the verification page
                    if not any(indicator in browser.current_url.lower() for indicator in ["challenge", "signin/v2"]):
                        print("[INFO] Verification complete. Proceeding...")
                        return
                    time.sleep(10)
                
                print("[WARNING] Verification timeout reached. The script will proceed but may fail if verification wasn't completed.")
                return
            
            time.sleep(5)  # Wait 5 seconds between checks
        
        # If we've reached this point, no verification was needed
        print("[INFO] No 2-step verification detected or already completed.")
    except Exception as e:
        print(f"[WARNING] Error during verification check: {e}")
        print("[INFO] Continuing with login attempt...")

# For some reason, the location filters here require that you press them
# This means that unlike the other filters, you need to use ActionChains to simulate user interaction
def location_filter(browser, locationTab):
    locationTab.click()
    searchField = WebDriverWait(browser, 10).until(
        EC.element_to_be_clickable((By.CLASS_NAME, 'Select-input'))
    )
    actions = ActionChains(browser)
    actions.move_to_element(searchField).click().perform()

    time.sleep(1)
    locationStr = os.getenv('SEARCH_LOCATIONS')
    for location in locationStr.split(',') if locationStr else []:
        searchField.send_keys(location)
        time.sleep(3)
        actions.move_to_element(searchField).click().perform()
        first_child = WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "Select-option"))
        )
        first_child.click()
        time.sleep(1)

# Filter out the jobs using the list provided
def job_filter(browser, jobTab, indexedJob):
    jobTab.click()

    try:
        checkboxInput = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.XPATH, "//span[text()='Is not any of']/preceding::div[@data-input='checkbox']"))
        )
        data_cy_status = checkboxInput.get_attribute('data-cy-status')
        if data_cy_status == 'unchecked':
            checkboxInput.click()
    
    except:
        print('Using layout where the inputs are regular')

    # Insert the job titles as filters
    inputFields = WebDriverWait(browser, 10).until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, 'Select-input'))
    )

    excludedJobTitlesStr = os.getenv('EXCLUDE_JOBS')
    for excJob in excludedJobTitlesStr.split(',') if excludedJobTitlesStr else []:
        inputFields[1].send_keys(excJob)
        first_child = WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "Select-option"))
        )
        first_child.click()
        time.sleep(1)
    # jobTitlesStr = os.getenv('JOB_TITLES')
    # Load the job titles first
    # for job in jobTitlesStr.split(',') if jobTitlesStr else []:
    inputFields[0].send_keys(indexedJob)
    first_child = WebDriverWait(browser, 10).until(
        EC.element_to_be_clickable((By.CLASS_NAME, "Select-option"))
    )
    first_child.click()
    time.sleep(1)

    # Open the tab
    cSuiteBtn = WebDriverWait(browser, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//div[div/span[text()='Departments & Job Function']]"))
    )
    cSuiteBtn.click()
    # Expand C-suite options
    cSuiteOption = WebDriverWait(browser, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//div[text()='C-Suite']"))
    )
    cSuiteOption.click()
    # Executive button
    executiveBtn = WebDriverWait(browser, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//div[text()='Executive']"))
    )
    executiveBtn.click()
    # Founder button
    founderBtn = WebDriverWait(browser, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//div[text()='Founder']"))
    )
    founderBtn.click()
    
def industryFilter(browser, industryTab):
    industryTab.click()

    # Wait for the search field to be clickable
    searchField = WebDriverWait(browser, 10).until(
        EC.element_to_be_clickable((By.CLASS_NAME, 'Select-input'))
    )

    actions = ActionChains(browser)
    actions.move_to_element(searchField).click().perform()

    time.sleep(1)

    # Get industry keywords from environment variable
    locationStr = os.getenv('INDUSTRY_KEYWORDS')

    for industry in locationStr.split(',') if locationStr else []:
        # Re-fetch the search field element before interacting with it
        searchField = WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, 'Select-input'))
        )

        actions.move_to_element(searchField).click().perform()
        
        # Clear the search field before entering new text
        searchField.clear()
        searchField.send_keys(industry)
        time.sleep(3)
        
        # Ensure the element is clicked before interacting
        actions.move_to_element(searchField).click().perform()

        # Wait for the "real estate" option to be present in the DOM
        first_child = WebDriverWait(browser, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, f"//div[contains(@class, 'Select-option') and normalize-space(text())='{industry}']"))
        )

        # Once it's present, wait for it to be clickable
        first_child = WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable(first_child[0])
        )
        
        first_child.click()
        time.sleep(1)

def companySizeFilters(browser, companySizeTab):
    companySizeTab.click()

    sizes = os.getenv('COMPANY_SIZE')
    if sizes:
        for size in sizes.split(','):
            time.sleep(3)
            cSuiteOption = WebDriverWait(browser, 10).until(
                EC.element_to_be_clickable((By.XPATH, f"//span[text()='{size}']/ancestor::span/preceding-sibling::div"))
            )
            cSuiteOption.click()

def show_all_emails(browser):
    allEmailButtons = browser.find_elements(By.XPATH, "//button[span[text()='Access email']]")

    for emailButton in allEmailButtons:
        emailButton.click()
        WebDriverWait(browser, 10).until(
            EC.invisibility_of_element_located(emailButton)
        )

def collect_data(browser, dataList, dataListClean, shouldCollectEmail):
    # Set based on the free limit of the service
    for pageNumber in range(3):
        
        for x in range(25):
            firstRow = WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.ID, 'table-row-' + str(x)))
            )
            dataRow = firstRow.find_elements(By.CLASS_NAME, 'zp_KtrQp')

            currRowData = []
            for cell in dataRow:
                currRowData.append(cell.text)

            # Need to ensure that the LinkedIn profile link exists for this row
            linkedInHref = 'N/A'
            if(len(firstRow.find_elements(By.CSS_SELECTOR, "i.zp-icon.apollo-icon.apollo-icon-linkedin")) > 0):
                linkedInHref = firstRow.find_element(By.CSS_SELECTOR, "i.zp-icon.apollo-icon.apollo-icon-linkedin").find_element(By.XPATH, "..").get_attribute("href")
            currRowData[6] = linkedInHref
            # There tends to be an empty element at the start of each row
            currRowData.pop(0)
            
            if(shouldCollectEmail):
                show_all_emails(firstRow)

            # Check if the email is personal and discard if so
            email_regex = r'\b[A-Za-z0-9._%+-]+@(gmail\.com|hotmail\.com|outlook\.com|yahoo\.com|aol\.com)\b'
            if(currRowData[3] != 'Access email' and re.match(currRowData[3], email_regex)):
                continue

            dataList.append(currRowData)
            # Now for the cleaned data
            currRowCleaned = copy.deepcopy(currRowData)
            # Original Cleaning process
            firstName = currRowCleaned[0].split(' ')[0]
            lastName = currRowCleaned[0].split(' ')[-1]
            currRowCleaned.pop(0)
            currRowCleaned.insert(0, lastName)
            currRowCleaned.insert(0, firstName)
            currRowCleaned.pop()
            currRowCleaned.pop()
            currRowCleaned.pop()
            currRowCleaned.pop(-2)
            currRowCleaned.pop(-2) # Empty column
            # Extra Cleaning to match the standard format
            currRowCleaned.pop() # Remove Location
            currRowCleaned.pop(3) # Remove Company
            dataListClean.append(currRowCleaned)

        # Navigate to next page
        nextPageBtn = WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.zp_qe0Li.zp_S5tZC > .apollo-icon-chevron-arrow-right'))
        )
        nextPageBtn.click()

def ApolloScraper(file_manager=None):
    print('[INFO] Loading configuration')
    # Point towards the .env file that contains the config
    envPath = Path(__file__).resolve().parents[1] / 'config' / '.env'

    if not load_dotenv(dotenv_path=envPath):
        raise FileNotFoundError(f"[Error] .env file not found at {envPath}")
    else:
        print(f"[INFO] Successfully loaded .env file from {envPath}")

    # Need accounts equal to the number of jobs
    accountsList = os.getenv('GOOGLE_EMAILS').split(',')
    passwordsList = os.getenv('GOOGLE_PASSWORDS').split(',')
    jobsList = os.getenv('JOB_TITLES').split(',')

    assert(len(accountsList) >= len(jobsList))

    # Define output directory - use file_manager if provided
    if file_manager:
        output_dir = file_manager.get_apollo_path().parent
    else:
        output_dir = Path(__file__).resolve().parents[1] / 'output'
        
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    results_files = []  # Track output files

    try:
        for index in range(len(jobsList)):
            userDataList = []
            userDataListClean = []

            try:
                browser = uc.Chrome()

                browser.get('https://app.apollo.io/#/login')

                # Find the Login with Google button
                print('[INFO] Attempting Google Login')
                elem = WebDriverWait(browser, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button.zp-button.zp_GGHzP.zp_Kbe5T.zp_PLp2D.zp_rduLJ.zp_g5xYz"))
                )
                elem.click()
                
                # Login using Google
                login_google(browser, accountsList[index], passwordsList[index])

                # Navigate to the appropriate tab
                peopleTab = WebDriverWait(browser, 30).until(
                    EC.element_to_be_clickable((By.ID, 'side-nav-people'))
                )
                peopleTab.click()
                time.sleep(4)

                # Get the filter tabs
                tabs = browser.find_elements(By.CSS_SELECTOR, 'div.zp-accordion-header.zp_r3aQ1')
                
                # Filter Industry
                print('[INFO] Setting industry filters')
                industryFilter(browser, browser.find_element(By.XPATH, "//span[text()='Industry & Keywords']/parent::*/parent::*"))

                print('[INFO] Setting company size filters')
                companySizeFilters(browser, browser.find_element(By.XPATH, "//span[text()='# Employees']/parent::*/parent::*"))
                
                # Filter locations
                print('[INFO] Setting location filters')
                location_filter(browser, tabs[5])

                print('[INFO] Setting job filters')
                # Filter required jobs
                job_filter(browser, tabs[3], jobsList[index])

                print('[INFO] Setting email filters')
                # Only include verified emails
                tabs[2].click()
                browser.find_element(By.CLASS_NAME, 'zp_vcdPP').click()
                
                print('[INFO] Scrapping data')
                
                # Collect all the user data into a list for CSV/JSON storage
                isCollectEmails = bool(strtobool(os.getenv('COLLECT_EMAILS')))
                collect_data(browser, userDataList, userDataListClean, isCollectEmails)

            except Exception as er:
                print(f'[ERROR] Failure in task number {index}: {er}')

            finally:
                # Use file_manager paths if available
                if file_manager:
                    raw_file = file_manager.get_apollo_path(f'ApolloRaw{index}.csv')
                    cleaned_file = file_manager.get_apollo_path(f'ApolloCleaned{index}.csv')
                else:
                    raw_file = output_dir / f'ApolloRaw{index}.csv'
                    cleaned_file = output_dir / f'ApolloCleaned{index}.csv'
                
                print('[INFO] Generating raw csv files')
                # Write the output to a csv file
                with open(raw_file, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    # Load the headers first before writing
                    headersStr = os.getenv('ROW_HEADERS')
                    headers = headersStr.split(',') if headersStr else []
                    # Write to the csv file
                    writer.writerow(headers)
                    writer.writerows(userDataList)

                print('[INFO] Generating cleaned csv files')
                # Write the cleaned csv file
                with open(cleaned_file, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    # Load the headers first before writing
                    headersStr = os.getenv('ROW_HEADERS_CLEAN')
                    headers = headersStr.split(',') if headersStr else []
                    # Write to the csv file
                    writer.writerow(headers)
                    # userDataListClean
                    writer.writerows(userDataListClean)
                
                # Track output files
                results_files.append(str(cleaned_file))
                browser.quit()
        
    except FileNotFoundError as fnfe:
        print(f'[ERROR] {fnfe}')
        return None

    except NoSuchElementException as nse:
        print(f"[ERROR] Failed to find an element in the browser while scraping: {nse}")
        return None

    except TimeoutError as te:
        print(f'[ERROR] Timed out while trying to find element: {te}')
        return None

    except Exception as e:
        print(f'[ERROR] An error occurred. Aborting: {e}')
        return None

    # At the end of the main try-except-finally block in ApolloScraper function
    finally:
        try:
            if file_manager:
                merged_file = file_manager.get_apollo_path('ApolloCleaned.csv')
            else:
                merged_file = output_dir / 'ApolloCleaned.csv'
                
            merge_cleaned(merged_file.parent, len(jobsList))

            # Process the cleaned data using the post process function
            print('[INFO] Standardising CSV output')
            if file_manager:
                filtered_file = file_manager.get_apollo_path('ApolloCleaned_Filtered.csv')
            else:
                filtered_file = output_dir / 'ApolloCleaned_Filtered.csv'
                
            clean_csv(merged_file, filtered_file)
            
            # Return the path to the final filtered file
            return str(filtered_file)

        except Exception as e:
            print(f"[WARNING] Error during final processing: {e}")
            # Still try to return something useful
            if results_files:
                return results_files[0]  # Return at least one of the output files
            return None

        finally:
            print("[INFO] Apollo scraping process completed")
            if 'browser' in locals() and browser:
                try:
                    browser.quit()
                    print("[INFO] Browser closed")
                except Exception as e:
                    print(f"[INFO] Browser may have already closed: {e}")