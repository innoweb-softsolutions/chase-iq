import pandas as pd
import re
from pathlib import Path

def merge_cleaned(input_directory, length):
    file_paths = []
    for i in range(length):
        file_paths.append(Path(input_directory) / f'ApolloCleaned{i}.csv')

    # Read and merge CSV files
    df_list = [pd.read_csv(file) for file in file_paths if file.exists()]
    
    if not df_list:
        print("[WARNING] No files found to merge")
        return
        
    merged_df = pd.concat(df_list, ignore_index=True)

    # Remove duplicate entries
    merged_df = merged_df.drop_duplicates()
    
    # Create a new DataFrame with the LinkedIn column structure
    linkedin_columns = [
        "role", "company", "location", "email", "website", 
        "profile_url", "linkedin_url", "domain", 
        "first_name", "last_name", "phone"
    ]
    
    standardized_df = pd.DataFrame(columns=linkedin_columns)
    
    # Map existing columns
    for col in linkedin_columns:
        if col in merged_df.columns:
            standardized_df[col] = merged_df[col]
        else:
            standardized_df[col] = ""
            
    # IMPORTANT: Map LinkedIn URLs from misc column
    if "misc" in merged_df.columns:
        standardized_df["linkedin_url"] = merged_df["misc"]
        
    # IMPORTANT: Create website URLs from domain
    if "domain" in merged_df.columns:
        standardized_df["website"] = "https://" + merged_df["domain"]

    # Save the standardized DataFrame
    output_file = Path(input_directory) / 'ApolloCleaned.csv'
    standardized_df.to_csv(output_file, index=False)

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
    
    # Create a new DataFrame with the LinkedIn column structure
    linkedin_columns = [
        "role", "company", "location", "email", "website", 
        "profile_url", "linkedin_url", "domain", 
        "first_name", "last_name", "phone"
    ]
    
    standardized_df = pd.DataFrame(columns=linkedin_columns)
    
    # Map existing columns to the standardized structure
    column_mapping = {
        "first_name": "first_name",
        "last_name": "last_name",
        "email": "email",
        "domain": "domain",
        "phone": "phone",
        "linkedin_url": "linkedin_url"  # ADDED: Preserve LinkedIn URLs
    }
    
    # Copy data from filtered_df to standardized_df
    for apollo_col, linkedin_col in column_mapping.items():
        if apollo_col in filtered_df.columns:
            standardized_df[linkedin_col] = filtered_df[apollo_col]
    
    # Set "role" from filtered_df if it exists
    if "role" in filtered_df.columns:
        standardized_df["role"] = filtered_df["role"]
    
    # Map any additional columns that might exist
    if "misc" in filtered_df.columns:
        standardized_df["company"] = filtered_df["misc"]  # Map misc to company if applicable
    
    # Set default values for missing columns
    for col in linkedin_columns:
        if col not in standardized_df.columns or standardized_df[col].isnull().all():
            standardized_df[col] = ""
    
    # Save the standardized DataFrame to output file
    standardized_df.to_csv(output_file, index=False)
    
    print(f"[INFO] Cleaning complete. {len(df) - len(filtered_df)} rows removed.")
    # print(f"Cleaned file saved as: {output_file}")