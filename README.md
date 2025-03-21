# LinkedIn Sales Navigator Scraper

A Python-based automation tool that scrapes LinkedIn Sales Navigator for profile data using Selenium.

## Overview

This tool allows you to automatically scrape LinkedIn Sales Navigator search results for contact information and profile data, targeting specific keywords (currently configured for "Real Estate Email").

## Features

- Automated login to LinkedIn Sales Navigator
- Cookie storage for session persistence
- Configurable user agent rotation
- Adjustable scraping parameters
- Headless browser mode option

## Prerequisites

- Python 3.10+
- Chrome/Chromium browser
- Chrome WebDriver

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

3. Set up your LinkedIn credentials in the configuration file.

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

Run the main script from the project root directory:

```bash
python main.py
```

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
6. Save results to CSV in the `output` directory

## Dependencies

- selenium==4.29.0
- undetected-chromedriver==3.5.5
- pandas==2.2.3
- fake-useragent==2.1.0

## Important Notes

- Use this tool responsibly and in accordance with LinkedIn's terms of service
- Excessive scraping may result in account limitations or bans
- The script includes built-in delays and user agent rotation to avoid detection
- Debug screenshots are automatically saved in `output/screenshots/` if errors occur
- Logs are stored in the `logs/` directory with timestamps

## Legal Disclaimer

This tool is provided for educational purposes only. Users are responsible for ensuring their use of this software complies with LinkedIn's terms of service and relevant laws. The authors are not responsible for any misuse of this software.

## License

MIT License
