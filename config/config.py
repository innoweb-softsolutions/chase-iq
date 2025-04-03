# LinkedIn Sales Navigator Scraper Configuration

# LinkedIn Credentials
LINKEDIN_EMAIL = "Wardhahaider16@gmail.com"
LINKEDIN_PASSWORD = "fucktard23hobo"

# URLs
SALES_NAV_URL = "https://www.linkedin.com/sales/search/people?query=(recentSearchParam%3A(id%3A4276071778%2CdoLogHistory%3Atrue)%2Cfilters%3AList((type%3ACOMPANY_HEADCOUNT%2Cvalues%3AList((id%3AC%2Ctext%3A11-50%2CselectionType%3AINCLUDED)%2C(id%3AD%2Ctext%3A51-200%2CselectionType%3AINCLUDED)))%2C(type%3ACURRENT_TITLE%2Cvalues%3AList((id%3A8%2Ctext%3AChief%2520Executive%2520Officer%2CselectionType%3AINCLUDED)%2C(id%3A5%2Ctext%3ADirector%2CselectionType%3AINCLUDED)%2C(id%3A35%2Ctext%3AFounder%2CselectionType%3AINCLUDED)%2C(id%3A68%2Ctext%3AChief%2520Financial%2520Officer%2CselectionType%3AEXCLUDED)%2C(id%3A1%2Ctext%3AOwner%2CselectionType%3AINCLUDED)%2C(id%3A195%2Ctext%3ACo-Owner%2CselectionType%3AINCLUDED)%2C(id%3A381%2Ctext%3AReal%2520Estate%2520Agent%2CselectionType%3AEXCLUDED)%2C(id%3A1042%2Ctext%3AReal%2520Estate%2520Broker%2CselectionType%3AEXCLUDED)%2C(id%3A8022%2Ctext%3AProfessional%2520Realtor%2CselectionType%3AEXCLUDED)%2C(id%3A3265%2Ctext%3ACommercial%2520Real%2520Estate%2520Specialist%2CselectionType%3AEXCLUDED)%2C(id%3A7760%2Ctext%3ALicensed%2520Real%2520Estate%2520Agent%2CselectionType%3AINCLUDED)%2C(id%3A916%2Ctext%3AInvestor%2CselectionType%3AEXCLUDED)%2C(id%3A2%2Ctext%3AManager%2CselectionType%3AEXCLUDED)%2C(id%3A50%2Ctext%3ASenior%2520Manager%2CselectionType%3AEXCLUDED)%2C(id%3A167%2Ctext%3AEmployee%2CselectionType%3AEXCLUDED)%2C(text%3A%2522Chief%2520Executive%2520Officer%2522%2CselectionType%3AINCLUDED)%2C(text%3ACEO%2520NOT%2520Assistant%2CselectionType%3AINCLUDED)%2C(text%3A%2522Co-Founder%2522%2CselectionType%3AINCLUDED)%2C(text%3ADirector%2520NOT%2520Deputy%2CselectionType%3AINCLUDED)%2C(text%3ADirector%2520NOT%2520Assistant%2CselectionType%3AINCLUDED)%2C(text%3ACEO%2520NOT%2520PA%2CselectionType%3AINCLUDED)%2C(text%3ACEO%2520NOT%2520%2522Personal%2520Assistant%2522%2CselectionType%3AINCLUDED)))%2C(type%3ASENIORITY_LEVEL%2Cvalues%3AList((id%3A220%2Ctext%3ADirector%2CselectionType%3AINCLUDED)%2C(id%3A320%2Ctext%3AOwner%2520%252F%2520Partner%2CselectionType%3AINCLUDED)%2C(id%3A300%2Ctext%3AVice%2520President%2CselectionType%3AINCLUDED)%2C(id%3A120%2Ctext%3ASenior%2CselectionType%3AINCLUDED)))%2C(type%3AREGION%2Cvalues%3AList((id%3A103644278%2Ctext%3AUnited%2520States%2CselectionType%3AINCLUDED)%2C(id%3A101165590%2Ctext%3AUnited%2520Kingdom%2CselectionType%3AINCLUDED)%2C(id%3A102393603%2Ctext%3AAsia%2CselectionType%3AEXCLUDED)%2C(id%3A103537801%2Ctext%3AAfrica%2CselectionType%3AEXCLUDED)))%2C(type%3AINDUSTRY%2Cvalues%3AList((id%3A44%2Ctext%3AReal%2520Estate%2CselectionType%3AINCLUDED)%2C(id%3A1770%2Ctext%3AReal%2520Estate%2520Agents%2520and%2520Brokers%2CselectionType%3AINCLUDED)%2C(id%3A1757%2Ctext%3AReal%2520Estate%2520and%2520Equipment%2520Rental%2520Services%2CselectionType%3AEXCLUDED)))%2C(type%3AFUNCTION%2Cvalues%3AList((id%3A23%2Ctext%3AReal%2520Estate%2CselectionType%3AINCLUDED)))))&sessionId=rbFgcAnmT2y3AxmM7P5AJA%3D%3D&viewAllFilters=true"
COOKIE_FILE = "config/cookies.pkl"

# Browser Settings
HEADLESS_MODE = False
USER_AGENT_ROTATION = True

# Scraping Settings
MAX_PROFILES = 3
MAX_PAGES = 20  # Maximum number of pages to scrape
PAGE_LOAD_TIMEOUT = 5
DELAY_BETWEEN_REQUESTS = 2  # seconds

# Currently Implemented Settings
SKIP_ALREADY_SCRAPED = False     # Skip profiles already scraped in previous runs
RETRY_FAILED_PROFILES = 1       # Number of times to retry failed profile scrapes
SCROLL_BEHAVIOR = "smart"       # Options: "none", "simple", "smart" (human-like)
SCREENSHOT_PROFILES = False     # Take screenshots of each profile for verification

# Login behavior configuration
KEYSTROKE_LOGIN = False  # Set to True to always use keystroke login instead of cookies

# Output Options
OUTPUT_FORMAT = "csv"           # Currently only CSV is fully supported
INCLUDE_TIMESTAMP = True        # Include timestamp in output filenames
DEDUPLICATE_RESULTS = True      # Remove duplicate profiles from results

# Performance Settings
REQUEST_TIMEOUT = 10           # Timeout for HTTP requests in seconds
RETRY_DELAY = 5                 # Delay between retries in seconds
ADD_RANDOM_DELAYS = True        # Add random delays between actions
SCRAPING_SPEED = "medium"       # Options: "slow", "medium", "fast" (affects delays)

# Data Processing Options (Used in Save to CSV)
NORMALIZE_COMPANY_NAMES = True  # Standardize company name formatting
NORMALIZE_JOB_TITLES = True     # Standardize job title formatting
REMOVE_EMOJI = True             # Remove emoji characters from text fields

# Archive Management
ARCHIVE_OLD_RESULTS = True      # Archive old results instead of overwriting
MAX_ARCHIVES_TO_KEEP = 10       # Number of archive files to keep
