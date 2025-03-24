# Facebook scraper configuration

# Facebook Credentials
FB_EMAIL = "tnkkdec@gmail.com"  # Facebook login email
FB_PASSWORD = "ys26U9t.YX5cP@b"  # Facebook login password

# Target Groups/Pages (updated with real group IDs from your screenshots)
FB_GROUPS = [
    # Real estate groups you've joined
    "realestatemastermind",        # Real Estate Investing (433K members)
    "realestatebusinessowner",    # Real Estate Agent Mastermind Group (118K members)
    "realestateinvestors",        # Real Estate Investors (103K members)
    "1745604695704216",  # Real Estate Islamabad (19.6K members)
    "1772684086279447",  # Real Estate Advisors for Overseas Pakistanis (58.0K members)
    "736890122998087",   # Islamabad Real Estate (37.1K members)
    "isbrealeatemkt",    # Islamabad Real Estate Market (21.1K members)
    "701830767484785",   # Islamabad Real Estate/Property/Societies/Chakri Road/Ring Road (10.8K members)
]

FB_PAGES = [
    "zillow",                   # Zillow Real Estate
    "remax",                    # RE/MAX
    "KellerWilliamsRealty",     # Keller Williams Realty
    "CBInTheWorld",             # Coldwell Banker
    "BerkshireHathawayHomeServices" # Berkshire Hathaway Home Services
]

# Scraping Settings (increased delays to avoid flagging)
MAX_POSTS = 40          # Adjusted to get enough posts without hitting limits
POSTS_PER_PAGE = 10     # Standard posts per page
TIMEOUT = 90            # Increased timeout for better reliability
MAX_PAGES = 2           # Reduced to avoid being flagged
USE_BROWSER = True      # Use browser fallback when needed
BROWSER_TYPE = "chrome" # Browser type
HEADLESS = True         # Headless mode
DELAY_BETWEEN_REQUESTS = 12  # Significantly increased delay to avoid detection

# Keywords to extract relevant posts (real estate focus)
KEYWORDS = [
    "real estate agent",
    "property dealer",
    "real estate broker",
    "property manager",
    "real estate investor",
    "property consultant",
    "realtor",
    "property advisor"
]

# Output Settings
OUTPUT_DIR = "output"