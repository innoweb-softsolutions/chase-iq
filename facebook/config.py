# Facebook scraper configuration

# Facebook Credentials (optional)
FB_EMAIL = None  # Set to your email to enable authenticated scraping
FB_PASSWORD = None  # Set to your password to enable authenticated scraping

# Target Groups/Pages
FB_GROUPS = [
    # Real estate investment and agent groups
    "realestateagentscommunity",
    "realestateinvestmentclub",
    "realestateinvestorsnetwork",
    "flippinghousesgroup",
    "firsttimehomebuyersgroup",
    "brrrinvestingstrategies"
]

FB_PAGES = [
    # Real estate experts, coaches, and gurus
    "grantcardone",
    "robertkiyosaki",
    "tonirobbins",
    "realestateinvestingtoday",
    "coachcarson",
    "biggerpockets"
]

# Scraping Settings
MAX_POSTS = 100  # Increased for better coverage
POSTS_PER_PAGE = 20  # Number of posts to request per page
TIMEOUT = 60  # Request timeout in seconds
MAX_PAGES = 5  # Maximum number of pages to scrape per group/page
USE_BROWSER = True  # Enable browser fallback for better results
BROWSER_TYPE = "chrome"  # Browser to use when USE_BROWSER is True
HEADLESS = True  # Run browser in headless mode
DELAY_BETWEEN_REQUESTS = 3  # Delay between requests to avoid rate limiting

# Keywords to extract relevant posts (real estate focus)
KEYWORDS = [
    "real estate agent",
    "real estate broker",
    "property manager",
    "real estate investor",
    "BRR",
    "flip houses",
    "first time buyers",
    "realtor",
    "real estate coach",
    "real estate expert"
]

# Output Settings
OUTPUT_DIR = "output"  # Directory to save CSV files