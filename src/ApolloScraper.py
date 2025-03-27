from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from .ApolloCSVCleaner import clean_csv
import undetected_chromedriver as uc
from distutils.util import strtobool
from dotenv import load_dotenv
from pathlib import Path
import time
import copy
import csv
import os
import re

# Fills in the user details and presses login
def login_google(browser):
    loginID = WebDriverWait(browser, 10).until(
        EC.element_to_be_clickable((By.ID, "identifierId"))
    )
    loginID.send_keys(os.getenv('GOOGLE_EMAIL'))
    loginID.send_keys(Keys.ENTER)

    passField = WebDriverWait(browser, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='password']"))
    )
    passField.send_keys(os.getenv('GOOGLE_PASSWORD'))
    passField.send_keys(Keys.ENTER)

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
def job_filter(browser, jobTab):
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
    jobTitlesStr = os.getenv('JOB_TITLES')
    # Load the job titles first
    for job in jobTitlesStr.split(',') if jobTitlesStr else []:
        inputFields[0].send_keys(job)
        first_child = WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "Select-option"))
        )
        first_child.click()
        time.sleep(1)

    # Only include C-Suite results
    cSuiteBtn = WebDriverWait(browser, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//div[div/span[text()='Departments & Job Function']]"))
    )
    cSuiteBtn.click()
    time.sleep(3)
    cSuiteOption = WebDriverWait(browser, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//div[text()='C-Suite']/preceding-sibling::div"))
    )
    cSuiteOption.click()
    
def industryFilter(browser, industryTab):
    industryTab.click()

    # Insert the job titles as filters
    inputFields = WebDriverWait(browser, 10).until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, 'Select-input'))
    )

    industryKeywords = os.getenv('INDUSTRY_KEYWORDS')
    for industry in industryKeywords.split(',') if industryKeywords else []:
        inputFields[0].send_keys(industry)
        first_child = WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "Select-option"))
        )
        first_child.click()
        time.sleep(1)

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

        # Assuming there are 25 records in each page
        if(shouldCollectEmail):
            print('[INFO] Collecting Emails')
            # Wait for the loading to stop before collecting the buttons
            WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.ID, 'table-row-0'))
            )
            show_all_emails(browser)
        else:
            print('[INFO] Skipping email collection (enable from settings)')
        
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

def ApolloScraper():
    print('[INFO] Loading configuration')
    # Point towards the .env file that contains the config
    envPath = Path(__file__).resolve().parents[1] / 'config' / '.env'

    if not load_dotenv(dotenv_path=envPath):
        raise FileNotFoundError(f"[Error] .env file not found at {envPath}")
    else:
        print(f"[INFO] Successfully loaded .env file from {envPath}")

    browser = uc.Chrome()

    try:
        browser.get('https://app.apollo.io/#/login')

        # Find the Login with Google button
        print('[INFO] Attempting Google Login')
        elem = WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.zp-button.zp_GGHzP.zp_Kbe5T.zp_PLp2D.zp_rduLJ.zp_g5xYz"))
        )
        elem.click()
        
        # Login using Google
        login_google(browser)

        # Navigate to the appropriate tab
        peopleTab = WebDriverWait(browser, 30).until(
            EC.element_to_be_clickable((By.ID, 'side-nav-people'))
        )
        peopleTab.click()
        time.sleep(4)

        print('[INFO] Setting location filters')
        # Get the filter tabs
        tabs = browser.find_elements(By.CSS_SELECTOR, 'div.zp-accordion-header.zp_r3aQ1')
        
        # Filter locations
        location_filter(browser, tabs[5])

        # Filter Industry
        print('[INFO] Setting industry filters')
        industryFilter(browser, tabs[7])

        print('[INFO] Setting job filters')
        # Filter required jobs
        job_filter(browser, tabs[3])

        print('[INFO] Setting email filters')
        # Only include verified emails
        tabs[2].click()
        browser.find_element(By.CLASS_NAME, 'zp_vcdPP').click()
        
        print('[INFO] Scrapping data')
        userDataList = []
        userDataListClean = []
        
        # Collect all the user data into a list for CSV/JSON storage
        isCollectEmails = bool(strtobool(os.getenv('COLLECT_EMAILS')))
        collect_data(browser, userDataList, userDataListClean, isCollectEmails)

        output_dir = Path(__file__).resolve().parents[1] / 'output'
        print('[INFO] Generating raw csv files')
        # Write the output to a csv file
        with open(output_dir / 'ApolloRaw.csv', 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            # Load the headers first before writing
            headersStr = os.getenv('ROW_HEADERS')
            headers = headersStr.split(',') if headersStr else []
            # Write to the csv file
            writer.writerow(headers)
            writer.writerows(userDataList)

        print('[INFO] Generating cleaned csv files')
        # Write the cleaned csv file
        with open(output_dir / 'ApolloCleaned.csv', 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            # Load the headers first before writing
            headersStr = os.getenv('ROW_HEADERS_CLEAN')
            headers = headersStr.split(',') if headersStr else []
            # Write to the csv file
            writer.writerow(headers)
            # userDataListClean
            writer.writerows(userDataListClean)

        # Process the cleaned data using the post process function
        print('[INFO] Standardising CSV output')
        cleanFilePath = Path(__file__).resolve().parents[1] / 'output' / 'ApolloCleaned.csv'
        cleanOutputPath = Path(__file__).resolve().parents[1] / 'output' / 'ApolloCleaned_Filtered.csv'
        clean_csv(cleanFilePath, cleanOutputPath)

        # print('Everything went well!')
        
    except FileNotFoundError as fnfe:
        print(fnfe)

    except NoSuchElementException:
        print("[Error] Failed to find an element in the browser while scraping. Aborting.")

    except TimeoutError:
        print('[ERROR] Timed out while trying to find element.')

    except Exception as e:
        print('[ERROR] An error occurred. Aborting.')

    finally:
        print("Completed")
        browser.quit()
