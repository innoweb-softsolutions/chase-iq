# LinkedIn Sales Navigator Scraper Configuration

# LinkedIn Credentials
LINKEDIN_EMAIL = "your_email@example.com"
LINKEDIN_PASSWORD = "your_password"

# URLs
SALES_NAV_URL = "https://www.linkedin.com/sales/search/people?query=(keywords:Real%20Estate%20Email)"
COOKIE_FILE = "config/cookies.pkl"

# Browser Settings
HEADLESS_MODE = False
USER_AGENT_ROTATION = True

# Scraping Settings
MAX_PROFILES = 50
PAGE_LOAD_TIMEOUT = 30
DELAY_BETWEEN_REQUESTS = 3  # seconds
