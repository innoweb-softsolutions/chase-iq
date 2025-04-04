# CQ

A Python-based automation tool that scrapes LinkedIn Sales Navigator for profile data using Selenium.

## Overview

This tool allows you to automatically scrape LinkedIn Sales Navigator search results for contact information and profile data, targeting specific keywords. It supports multiple data sources including LinkedIn Sales Navigator, Apollo, and LeadRocks.

## Features

- Automated login to LinkedIn Sales Navigator
- Cookie storage for session persistence
- Configurable user agent rotation
- Adjustable scraping parameters
- Headless browser mode option
- Multiple data source support:
  - LinkedIn Sales Navigator scraping
  - Apollo data integration
  - LeadRocks enrichment and export
- Parallel scraping from multiple sources
- Data merging and deduplication
- Email verification via Snov.io and Hunter.io
- Phone number validation via ClearoutPhone API

## Prerequisites

- Python 3.10+
- Chrome/Chromium browser
- Chrome WebDriver
- LeadRocks Chrome extension (for LeadRocks functionality)
- Snov.io API credentials
- Hunter.io API credentials

## Installation

1. Clone this repository:
```bash
git clone https://github.com/innoweb-softsolutions/chase-iq.git
cd chase-iq
```

2. Create a virtual environment:

Using Conda:
```bash
conda create -n chase-iq python=3.10
conda activate chase-iq
```

OR using venv:
```bash
python -m venv venv
source venv/bin/activate  # On Linux/Mac
venv\Scripts\activate     # On Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up your LinkedIn credentials in the configuration file.

5. Install and configure the LeadRocks Chrome extension:
   - Install from Chrome Web Store
   - Log in to your LeadRocks account
   - Ensure the extension has necessary permissions

## Project Structure

```
├── config/
│   ├── config.py         # Configuration settings
│   └── cookies.pkl       # Saved session cookies
├── output/
│   ├── screenshots/      # Debug screenshots
│   └── *.csv            # Scraped lead data
├── src/
│   ├── scraper.py       # Core scraping logic
│   ├── LeadRocksPipeLine.py  # LeadRocks integration
│   └── utils/
│       └── helpers.py   # Helper functions
├── logs/                # Scraping logs
└── requirements.txt     # Python dependencies
```

## Configuration

Edit `config/config.py` to customize your scraping parameters:

```python
# LinkedIn Credentials
LINKEDIN_EMAIL = "your_email@example.com"
LINKEDIN_PASSWORD = "your_password"

# URLs
SALES_NAV_URL = "https://www.linkedin.com/sales/search/people?query=(keywords:Real%20Estate%20Email)"
COOKIE_FILE = "config/cookies.pkl"

# Browser Settings
HEADLESS_MODE = False      # Run browser in headless mode
USER_AGENT_ROTATION = True # Rotate user agents for each session

# Scraping Settings
MAX_PROFILES = 50         # Maximum number of profiles to scrape
PAGE_LOAD_TIMEOUT = 30    # Page load timeout in seconds
DELAY_BETWEEN_REQUESTS = 3 # Delay between profile visits
```

## Usage

The tool can be run in several modes:

1. Full Pipeline (all sources):
```bash
python main.py
```

2. LinkedIn Sales Navigator Only:
```bash
python main.py --linkedin-only
```

3. Apollo Only:
```bash
python main.py --apollo-only
```

4. LeadRocks Only:
```bash
python main.py --leadrocks-only --search-query "real estate ceo US"  # For United States
python main.py --leadrocks-only --search-query "real estate ceo UK"  # For United Kingdom
```

5. LeadRocks with Phone Validation:
```bash
python main.py --leadrocks-only --search-query "real estate ceo US" --validate-phones
```

Additional Options:
- `--skip-snovio`: Skip Snov.io email finding
- `--skip-hunter`: Skip Hunter.io email verification
- `--input-csv`: Use existing CSV file instead of scraping
- `--validate-phones`: Validate phone numbers using ClearoutPhone API

The script will:
1. Attempt to login using saved cookies
2. Fall back to credentials if cookies fail
3. Navigate to Sales Navigator search results
4. Extract profile links based on search criteria
5. Visit each profile and extract:
   - Name
   - Title
   - Company
   - Email (if available)
   - Website (if available)
   - Team Size (LeadRocks only)
6. Enrich data using LeadRocks (when enabled)
7. Save results to CSV in the `output` directory
8. Merge data from multiple sources (when running full pipeline)
9. Verify and enrich emails using Snov.io and Hunter.io (unless skipped)

## Dependencies

Key dependencies include:
- selenium==4.29.0
- undetected-chromedriver==3.5.5
- pandas==2.2.3
- fake-useragent==2.1.0
- requests==2.32.3
- python-dotenv==1.0.1

## Important Notes

- Use this tool responsibly and in accordance with LinkedIn's terms of service
- Excessive scraping may result in account limitations or bans
- The script includes built-in delays and user agent rotation to avoid detection
- Debug screenshots are automatically saved in `output/screenshots/` if errors occur
- Logs are stored in the `logs/` directory with timestamps
- When using LeadRocks:
  - Ensure the Chrome extension is installed and logged in
  - Use "US" or "UK" for location (not "United States" or "United Kingdom")
  - Search query format: "[keywords] [title] [location]"
  - Example queries:
    - "real estate ceo US"
    - "software engineer UK"
    - "startup founder US"
  - Phone validation requires internet access and uses the ClearoutPhone API
  - Validation results are stored as JSON files alongside the CSV files
- API Keys:
  - Snov.io and Hunter.io API keys are required for email verification
  - ClearoutPhone API key is used for phone number validation
  - Store API keys securely in environment variables or config files

## Legal Disclaimer

This tool is provided for educational purposes only. Users are responsible for ensuring their use of this software complies with LinkedIn's terms of service and relevant laws. The authors are not responsible for any misuse of this software.

## License

MIT License
