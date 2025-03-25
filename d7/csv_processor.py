import os
import re
import csv
from pathlib import Path

# Define the columns to keep
DESIRED_COLUMNS = [
   "Name", 
    "Telephone", 
    "Email", 
    "Profile URL (LinkedIn)", 
    "Website", 
    "Role/Title", 
    "Company"
]

COLUMN_MAPPING = {
    "Name": ["Name", "BusinessName"],
    "Telephone": ["Telephone"],
    "Email": ["Email"],
    "Profile URL (LinkedIn)": ["Profile URL (LinkedIn)", "Linkedin"],
    "Website": ["Website", "WebsiteURL"],
    "Role/Title": ["Role/Title", "Title"],
    "Company": ["Company", "BusinessName"]
}

def extract_location_info(filename):
    """
    Extract location info from filename.
    Expected pattern: 'Real Estate Investor in Houston, TX (Report by).csv'
    """
    name_no_ext = os.path.splitext(filename)[0]
    match = re.search(r'in (.*) \(Report by\)', name_no_ext, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    else:
        # Fallback: use the filename without extension
        return name_no_ext

def is_valid_lead_email(email):
    """
    Returns True if the email is a valid lead email.
    Filters out emails that contain keywords typically used for generic or
    administrative addresses.
    """
    if not email:
        return False
    email_lower = email.lower()
    invalid_keywords = ["info", "noreply", "no-reply", "support", "sales", "admin", "contact","hello","advertising"]
    for keyword in invalid_keywords:
        if keyword in email_lower:
            return False
    return True

def map_row_columns(row):
    """
    Map values from the input row to the desired output columns using the COLUMN_MAPPING.
    For each desired column, the function checks each alternative source key in order.
    """
    new_row = {}
    for dest_col, alternatives in COLUMN_MAPPING.items():
        value = ""
        for key in alternatives:
            if key in row and row[key].strip():
                value = row[key].strip()
                break
        new_row[dest_col] = value
    return new_row

def process_csv_file(input_file, output_dir):
    """
    Process a raw CSV file by mapping and keeping only the desired columns.
    Rows with emails containing generic keywords (e.g. info, noreply) are skipped.
    Writes the processed CSV to output_dir with a "processed_" prefix.
    """
    filename = os.path.basename(input_file)
    output_file = os.path.join(output_dir, f"processed_{filename}")

    with open(input_file, mode='r', encoding='utf-8', newline='') as infile, \
         open(output_file, mode='w', encoding='utf-8', newline='') as outfile:
        
        reader = csv.DictReader(infile)
        writer = csv.DictWriter(outfile, fieldnames=DESIRED_COLUMNS)
        writer.writeheader()

        for row in reader:
            # Map the row to the desired schema.
            new_row = map_row_columns(row)
            email = new_row.get("Email", "")
            if not is_valid_lead_email(email):
                # Skip rows with invalid or generic email addresses
                continue
            writer.writerow(new_row)

    print(f"Processed '{filename}' -> '{output_file}'")
    return output_file

# Example usage:
if __name__ == "__main__":
    # Define the directories (adjust as needed)
    INPUT_DIR = "data"
    OUTPUT_DIR = "processed"
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    # Process all CSV files in the input directory
    for file in os.listdir(INPUT_DIR):
        if file.lower().endswith('.csv'):
            input_file = os.path.join(INPUT_DIR, file)
            process_csv_file(input_file, OUTPUT_DIR)
