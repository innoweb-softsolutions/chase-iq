# LinkedIn Sales Navigator Scraper Configuration

# LinkedIn Credentials
LINKEDIN_EMAIL = "your_email@example.com"
LINKEDIN_PASSWORD = "your_password"

# URLs
SALES_NAV_URL = "https://www.linkedin.com/sales/search/people?query=(recentSearchParam%3A(id%3A4276071778%2CdoLogHistory%3Atrue)%2Cfilters%3AList((type%3AFUNCTION%2Cvalues%3AList((id%3A23%2Ctext%3AReal%2520Estate%2CselectionType%3AINCLUDED)))%2C(type%3ACOMPANY_HEADCOUNT%2Cvalues%3AList((id%3AC%2Ctext%3A11-50%2CselectionType%3AINCLUDED)))%2C(type%3ACURRENT_TITLE%2Cvalues%3AList((id%3A8%2Ctext%3AChief%2520Executive%2520Officer%2CselectionType%3AINCLUDED)%2C(id%3A5%2Ctext%3ADirector%2CselectionType%3AINCLUDED)%2C(id%3A35%2Ctext%3AFounder%2CselectionType%3AINCLUDED)%2C(id%3A68%2Ctext%3AChief%2520Financial%2520Officer%2CselectionType%3AINCLUDED)%2C(id%3A1%2Ctext%3AOwner%2CselectionType%3AINCLUDED)%2C(id%3A195%2Ctext%3ACo-Owner%2CselectionType%3AINCLUDED)%2C(id%3A381%2Ctext%3AReal%2520Estate%2520Agent%2CselectionType%3AINCLUDED)%2C(id%3A1042%2Ctext%3AReal%2520Estate%2520Broker%2CselectionType%3AINCLUDED)%2C(id%3A8022%2Ctext%3AProfessional%2520Realtor%2CselectionType%3AINCLUDED)%2C(id%3A3265%2Ctext%3ACommercial%2520Real%2520Estate%2520Specialist%2CselectionType%3AINCLUDED)%2C(id%3A7760%2Ctext%3ALicensed%2520Real%2520Estate%2520Agent%2CselectionType%3AINCLUDED)%2C(id%3A916%2Ctext%3AInvestor%2CselectionType%3AINCLUDED)))%2C(type%3ASENIORITY_LEVEL%2Cvalues%3AList((id%3A220%2Ctext%3ADirector%2CselectionType%3AINCLUDED)%2C(id%3A320%2Ctext%3AOwner%2520%252F%2520Partner%2CselectionType%3AINCLUDED)%2C(id%3A300%2Ctext%3AVice%2520President%2CselectionType%3AINCLUDED)%2C(id%3A120%2Ctext%3ASenior%2CselectionType%3AINCLUDED)))%2C(type%3AREGION%2Cvalues%3AList((id%3A103644278%2Ctext%3AUnited%2520States%2CselectionType%3AINCLUDED)%2C(id%3A91000007%2Ctext%3AEMEA%2CselectionType%3AINCLUDED)))))&sessionId=rbFgcAnmT2y3AxmM7P5AJA%3D%3D&viewAllFilters=true"
COOKIE_FILE = "config/cookies.pkl"

# Browser Settings
HEADLESS_MODE = False
USER_AGENT_ROTATION = True

# Scraping Settings
MAX_PROFILES = 50
PAGE_LOAD_TIMEOUT = 30
DELAY_BETWEEN_REQUESTS = 3  # seconds
