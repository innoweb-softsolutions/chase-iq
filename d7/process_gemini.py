import os
import csv
import time
from csv_processor import extract_location_info
from gemini import check_email_role

def process_gemini_on_csv(processed_file, output_dir):
    """
    Read a processed CSV file, call Gemini API for each row using all available 
    information, and output a final CSV with two additional columns: 
    'Executive Role' and 'Role Justification'.
    
    The API is rate limited to 15 requests per minute.
    """
    filename = os.path.basename(processed_file)
    output_file = os.path.join(output_dir, f"final_{filename}")

    # Use filename to extract location information
    location_info = extract_location_info(filename)

    with open(processed_file, mode='r', encoding='utf-8', newline='') as infile, \
         open(output_file, mode='w', encoding='utf-8', newline='') as outfile:

        reader = csv.DictReader(infile)
          # Append the new column "Role/Title" to the existing fieldnames
        fieldnames = reader.fieldnames + ["Role/Title"]
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            email = row.get("Email", "").strip()
            if email:
                response_text = check_email_role(row, location_info)
                # Enforce rate limiting: wait 4 seconds per request (~15 per minute)
                time.sleep(4)
                # Since the Gemini API now returns a combined "Role/Title" field,
                # simply trim the response text.
                role_title = response_text.strip()
            else:
                role_title = "No email provided in row."
            # Set the new field with the combined role/title information
            row["Role/Title"] = role_title
            writer.writerow(row)

    print(f"Gemini processing complete for '{filename}' -> '{output_file}'")
    return output_file
