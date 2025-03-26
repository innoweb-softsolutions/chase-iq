import pandas as pd
import re
from pathlib import Path

def clean_csv(input_file, output_file):
    # Ensure input_file and output_file are strings (in case Path objects are passed)
    input_file = str(input_file)
    output_file = str(output_file)
    
    # Load the CSV file
    df = pd.read_csv(input_file, dtype=str)
    
    # Handle different column naming conventions
    column_mapping = {
        'First Name': 'first_name',
        'Last Name': 'last_name',
        'first name': 'first_name',
        'last name': 'last_name',
        'Email': 'email',
        'Phone': 'phone',
        'Phone Number': 'phone'
    }
    
    # Rename columns if they exist
    for old_col, new_col in column_mapping.items():
        if old_col in df.columns:
            df = df.rename(columns={old_col: new_col})
    
    # Check if we still need to split Name into first_name/last_name
    if 'first_name' not in df.columns and 'Name' in df.columns:
        try:
            # Split Name into first_name and last_name
            name_parts = df['Name'].str.split(' ', n=1, expand=True)
            if len(name_parts.columns) >= 2:
                df['first_name'] = name_parts[0]
                df['last_name'] = name_parts[1]
            else:
                # Handle single-word names
                df['first_name'] = name_parts[0]
                df['last_name'] = ''
        except Exception as e:
            print(f"[WARNING] Error splitting names: {e}")
    
    # Define regex pattern to filter single-letter names with optional dashes or periods
    single_letter_pattern = re.compile(r'^\s*[A-Z]\s*[-.]*\s*$', re.IGNORECASE)
    
    # Initialize filtered_df as a copy of the original
    filtered_df = df.copy()
    
    # Filter out rows where first_name or last_name match the pattern (if columns exist)
    if 'first_name' in filtered_df.columns:
        filtered_df = filtered_df[~filtered_df['first_name'].str.match(single_letter_pattern, na=False)]
    
    if 'last_name' in filtered_df.columns:
        filtered_df = filtered_df[~filtered_df['last_name'].str.match(single_letter_pattern, na=False)]
    
    # Remove rows where email is "No email" or "Access email" (if email column exists)
    if 'email' in filtered_df.columns:
        filtered_df = filtered_df[~filtered_df['email'].isin(['No email', 'Access email'])]
    
    # Extract domain from email (if email column exists)
    if 'email' in filtered_df.columns:
        filtered_df['domain'] = filtered_df['email'].str.extract(r'@(.+)')
    
    # Reorder columns to place 'domain' after 'phone' (if both exist)
    if 'phone' in filtered_df.columns and 'domain' in filtered_df.columns:
        cols = filtered_df.columns.tolist()
        phone_index = cols.index('phone')
        cols.insert(phone_index + 1, cols.pop(cols.index('domain')))
        filtered_df = filtered_df[cols]
    
    # Save the cleaned DataFrame to a new CSV file
    filtered_df.to_csv(output_file, index=False)
    
    print(f"[INFO] Cleaning complete. {len(df) - len(filtered_df)} rows removed.")