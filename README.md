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

- Python 3.6+
- Chrome/Chromium browser
- Chrome WebDriver

## Installation

1. Clone this repository:
```
git clone <repository-url>
cd SeleniumStarter
```

2. Install dependencies:
```
pip install -r requirements.txt
```

3. Set up your LinkedIn credentials in the configuration file.

## Configuration

Edit the configuration file at `SalesNav/config/config.py` to customize your scraping parameters:

```python
# LinkedIn Credentials
LINKEDIN_EMAIL = "your_email@example.com"
LINKEDIN_PASSWORD = "your_password"

# URLs
SALES_NAV_URL = "https://www.linkedin.com/sales/search/people?query=(keywords:Real%20Estate%20Email)"

# Browser Settings
HEADLESS_MODE = False
USER_AGENT_ROTATION = True

# Scraping Settings
MAX_PROFILES = 50
PAGE_LOAD_TIMEOUT = 30
DELAY_BETWEEN_REQUESTS = 3  # seconds
```

## Usage

Run the main script from the project root directory:

```
python SalesNav/main.py
```

## Important Notes

- Use this tool responsibly and in accordance with LinkedIn's terms of service.
- Excessive scraping may result in account limitations or bans.
- Consider adding delays between requests to avoid detection.
- Always use your own LinkedIn account credentials.

## Legal Disclaimer

This tool is provided for educational purposes only. Users are responsible for ensuring their use of this software complies with LinkedIn's terms of service and relevant laws. The authors are not responsible for any misuse of this software.

## License

[Include your license information here]
