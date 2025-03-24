import re
from google.generativeai import GenerativeModel, configure

# Your API key (replace if needed)
API_KEY = ""

def validate_email(email):
    """Validate email format using a regex."""
    pattern = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def create_prompt(row_info, location_info):
    """
    Create a dynamic prompt for the Gemini API using all the row information.
    The CSV row is expected to contain keys like BusinessName, Telephone, Email, 
    FacebookProfile, WebsiteURL, Linkedin, Address, City.
    
    The prompt instructs the API to determine if the email belongs to a company 
    executive and to return a structured response in the following format:
    
    Role: [Executive Role] ; Justification: [Your detailed justification]
    """
    details = "\n".join([f"{key}: {value}" for key, value in row_info.items()])
    email = row_info.get("Email", "")
    return f"""
Based on publicly available data only, analyze the following business information:
{details}

The email address provided is {email} from the {location_info} real estate sector.

Determine if this email belongs to a company executive (e.g. Director, CEO, Founder, CFO, Owner, or Co-owner). 
If it does, return the following structured response exactly in this format:

Role: [Executive Role] ; Justification: [Your detailed justification]

If no executive information is found, return a message clearly stating that no information was found.

Only use publicly available information.
"""

def check_email_role(row_info, location_info, model_name='gemini-2.0-flash'):
    """
    Use the Gemini API to check if the email (along with other provided row info)
    belongs to an executive. Returns the API response text.
    """
    email = row_info.get("Email", "")
    if not validate_email(email):
        return "Invalid email format. Please provide a valid email address."

    prompt = create_prompt(row_info, location_info)
    try:
        configure(api_key=API_KEY)
        model = GenerativeModel(model_name)
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"An error occurred: {str(e)}"
