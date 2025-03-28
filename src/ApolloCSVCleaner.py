import pandas as pd
import re
from pathlib import Path

def clean_csv(input_file, output_file):
    # Ensure input_file and output_file are strings (in case Path objects are passed)
    input_file = str(input_file)
    output_file = str(output_file)
    
    # Load the CSV file
    df = pd.read_csv(input_file, dtype=str)
    
    # Define regex pattern to filter single-letter names with optional dashes or periods
    single_letter_pattern = re.compile(r'^\s*[A-Z]\s*[-.]*\s*$', re.IGNORECASE)
    
    # Filter out rows where first_name or last_name match the pattern
    filtered_df = df[~df["first_name"].str.match(single_letter_pattern, na=False) &
                     ~df["last_name"].str.match(single_letter_pattern, na=False)]
    
    # Remove rows where email is "No email" or "Access email"
    filtered_df = filtered_df[~filtered_df["email"].isin(["No email", "Access email"])]
    
    # Extract domain from email
    filtered_df["domain"] = filtered_df["email"].str.extract(r'@(.+)')
    
    # Reorder columns to place 'domain' after 'phone'
    if "phone" in filtered_df.columns and "domain" in filtered_df.columns:
        cols = filtered_df.columns.tolist()
        phone_index = cols.index("phone")
        cols.insert(phone_index + 1, cols.pop(cols.index("domain")))
        filtered_df = filtered_df[cols]
    
    # Save the cleaned DataFrame to a new CSV file
    filtered_df.to_csv(output_file, index=False)
    
    print(f"[INFO] Cleaning complete. {len(df) - len(filtered_df)} rows removed.")
    # print(f"Cleaned file saved as: {output_file}")
