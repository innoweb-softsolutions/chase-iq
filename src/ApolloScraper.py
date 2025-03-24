from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import undetected_chromedriver as uc
from dotenv import load_dotenv
from distutils.util import strtobool
from pathlib import Path
import time
import copy
import csv
import os


# Fills in the user details and presses login
def login_google(browser):
    loginID = browser.find_element(By.ID, "identifierId")
    loginID.send_keys(os.getenv('GOOGLE_EMAIL'))
    loginID.send_keys(Keys.ENTER)

    time.sleep(3)

    passField = browser.find_element(By.CSS_SELECTOR, "input[type='password']")
    passField.send_keys(os.getenv('GOOGLE_PASSWORD'))
    passField.send_keys(Keys.ENTER)

    time.sleep(30)

# For some reason, the location filters here require that you press them
# This means that unlike the other filters, you need to use ActionChains to simulate user interaction
def location_filter(browser, locationTab):
    locationTab.click()
    searchField = browser.find_element(By.CLASS_NAME, 'Select-input')
    actions = ActionChains(browser)
    actions.move_to_element(searchField).click().perform()

    time.sleep(1)
    locationStr = os.getenv('SEARCH_LOCATIONS')
    for location in locationStr.split(',') if locationStr else []:
        searchField.send_keys(location)
        time.sleep(3)
        actions.move_to_element(searchField).click().perform()
        time.sleep(1)
        searchField.send_keys(Keys.ENTER)
        time.sleep(4)

# Filter out the jobs using the list provided
def job_filter(browser, jobTab):
    jobTab.click()
    
    # Insert the job titles as filters
    searchField = browser.find_element(By.CSS_SELECTOR, 'div.Select-placeholder')
    searchField = browser.find_element(By.CLASS_NAME, 'Select-input')
    jobTitlesStr = os.getenv('JOB_TITLES')
    # Load the job titles first
    for job in jobTitlesStr.split(',') if jobTitlesStr else []:
        searchField.send_keys(job)
        time.sleep(3)
        searchField.send_keys(Keys.ENTER)
        time.sleep(4)

    # Only include C-Suite results
    time.sleep(4)
    browser.find_element(By.XPATH, "//div[div/span[text()='Departments & Job Function']]").click()
    time.sleep(4)
    browser.find_element(By.XPATH, "//div[text()='C-Suite']/preceding-sibling::div").click()
    time.sleep(4)

def show_all_emails(browser):
    allEmailButtons = browser.find_elements(By.XPATH, "//button[span[text()='Access email']]")

    for emailButton in allEmailButtons:
        emailButton.click()
        time.sleep(6)

def collect_data(browser, dataList, dataListClean, shouldCollectEmail):
    # Set based on the free limit of the service
    for pageNumber in range(2):

        # Assuming there are 25 records in each page
        for x in range(25):
            firstRow = browser.find_element(By.ID, 'table-row-' + str(x))
            dataRow = firstRow.find_elements(By.CLASS_NAME, 'zp_KtrQp')

            if(shouldCollectEmail):
                print('[INFO] Collecting Emails')
                show_all_emails()
            else:
                print('[INFO] Skipping email collection (enable from settings)')
            
            currRowData = []
            for cell in dataRow:
                currRowData.append(cell.text)

            # There tends to be an empty element at the start of each row
            linkedInHref = firstRow.find_element(By.CSS_SELECTOR, "i.zp-icon.apollo-icon.apollo-icon-linkedin").find_element(By.XPATH, "..").get_attribute("href")
            currRowData[6] = linkedInHref
            currRowData.pop(0)
            dataList.append(currRowData)
            # Now for the cleaned data
            currRowCleaned = copy.deepcopy(currRowData)
            currRowCleaned.pop()
            currRowCleaned.pop()
            currRowCleaned.pop()
            currRowCleaned.pop(-2)
            currRowCleaned.pop(-2)
            dataListClean.append(currRowCleaned)

        # Navigate to next page
        browser.find_element(By.CSS_SELECTOR, 'button.zp_qe0Li.zp_S5tZC > .apollo-icon-chevron-arrow-right').click()
        time.sleep(7)


def ApolloScraper():
    print('[INFO] Loading configuration')
    # Point towards the .env file that contains the config
    envPath = Path(__file__).resolve().parents[1] / 'config' / '.env'
    # load_dotenv(dotenv_path=envPath)
    if not load_dotenv(dotenv_path=envPath):
        raise FileNotFoundError(f"Error: .env file not found at {envPath}")
    else:
        print(f"[INFO] Successfully loaded .env file from {envPath}")

    browser = uc.Chrome()

    try:
        browser.get('https://app.apollo.io/#/login')

        time.sleep(3)

        # Find the Login with Google button
        print('[INFO] Attempting Google Login')
        elem = browser.find_element(By.CSS_SELECTOR, "button.zp-button.zp_GGHzP.zp_Kbe5T.zp_PLp2D.zp_rduLJ.zp_g5xYz")
        elem.click()
        time.sleep(3)

        # Login using Google
        login_google(browser)

        # Navigate to the appropriate tab
        browser.find_element(By.ID, 'side-nav-people').click()
        time.sleep(4)

        print('[INFO] Setting location filters')
        # Get the filter tabs
        tabs = browser.find_elements(By.CSS_SELECTOR, 'div.zp-accordion-header.zp_r3aQ1')
        time.sleep(4)
        
        # Filter locations
        location_filter(browser, tabs[5])

        print('[INFO] Setting job filters')
        # Filter required jobs
        job_filter(browser, tabs[3])

        print('[INFO] Setting email filters')
        # Only include verified emails
        tabs[2].click()
        browser.find_element(By.CLASS_NAME, 'zp_vcdPP').click()
        time.sleep(4)

        print('[INFO] Scrapping data')
        userDataList = []
        userDataListClean = []
        time.sleep(6)

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
            writer.writerows(userDataListClean)

        print('Everything went well!')
        # time.sleep(600)

    except FileNotFoundError as fnfe:
        print(fnfe)

    except Exception as e:
        print(f"Ran into an error")

    finally:
        print("Completed")
        browser.quit()