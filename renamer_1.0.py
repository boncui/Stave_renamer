import os
import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# Constants
SHEET_NAME = "Copy of Independent Stave Company Data Collection (Responses)"
CREDENTIALS_PATH = "credentials.json"
OUTPUT_MAPPING_FILE = "stave_name_plus_count.txt"
LOCAL_IMAGES_DIRECTORY = "/Users/boncui/Desktop/Projects/Stave Project/Data"

def authenticate_google_sheets(credentials_path, sheet_name):
    """Authenticate and access Google Sheets."""
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scope)
    client = gspread.authorize(creds)
    return client.open(sheet_name).sheet1

def extract_filename_from_url(url):
    """
    Extract the filename from a Google Drive URL.
    Example URL: https://drive.google.com/file/d/10U78qPiM29p3Vsp4JiqCdXhT9drBtOKs/view
    """
    # Extract file ID from the URL
    file_id_match = re.search(r'/d/([^/]+)/', url)
    if not file_id_match:
        return None
    
    # Since we can't directly get the filename from the URL without additional API calls,
    # we'll extract what we can. In a real scenario, you might want to use the Drive API
    # to get the actual filename.
    
    # For the purpose of this script, we'll assume you have a way to match the file ID
    # with the actual filename (from your example: "17289132322424750858174835555844 - Brandon Wagner.jpg")
    
    # This is a placeholder. You would need to implement this based on your specific data structure.
    # For now, this returns None, and the actual mapping will need to come from the sheet data.
    return None

def extract_file_info_from_sheet(sheet):
    """
    Extract file names and stave counts from the Google Sheet.
    """
    # Get all records from the sheet
    records = sheet.get_all_records()
    
    # Convert to pandas DataFrame for easier manipulation
    df = pd.DataFrame(records)
    
    file_info = {}
    
    # Ensure the required columns exist
    if 'Upload Stave Pallet Photo' in df.columns and 'Stave Count' in df.columns:
        for index, row in df.iterrows():
            photo_url = row['Upload Stave Pallet Photo']
            stave_count = row['Stave Count']
            
            # Skip if any of these values are missing
            if pd.isna(photo_url) or pd.isna(stave_count) or not photo_url or not stave_count:
                continue
            
            # Extract file ID from URL
            file_id_match = re.search(r'/d/([^/]+)/', photo_url)
            if file_id_match:
                file_id = file_id_match.group(1)
                
                # From your example, we need to extract a filename like 
                # "17289132322424750858174835555844 - Brandon Wagner.jpg"
                # If this is part of the sheet data in another column, we would get it from there
                
                # For now, let's assume we have a function that can map file IDs to filenames
                # In practice, you might need to extract this differently
                
                # Attempt to extract the filename from the URL or file ID
                # This is a simplified example. You may need to adjust based on your actual data
                filename_parts = photo_url.split("/")
                if len(filename_parts) > 5:
                    # Try to use a pattern to extract the name
                    name_pattern = r'(\d+)\s*-\s*([^\.]+)'
                    for part in filename_parts:
                        match = re.search(name_pattern, part)
                        if match:
                            file_name = f"{match.group(1)} - {match.group(2)}"
                            file_info[file_name] = str(stave_count)
                            break
    
    return file_info

def save_mapping_to_file(file_info, output_path):
    """
    Save file name to stave count mappings to a text file
    """
    with open(output_path, 'w') as f:
        for file_name, stave_count in file_info.items():
            f.write(f"{file_name}|{stave_count}\n")
    
    print(f"Mapping saved to {output_path}")

def load_mapping_from_file(input_path):
    """
    Load file name to stave count mappings from a text file
    """
    file_info = {}
    
    if not os.path.exists(input_path):
        print(f"Warning: Mapping file {input_path} not found.")
        return file_info
    
    with open(input_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                parts = line.split('|')
                if len(parts) == 2:
                    file_name, stave_count = parts
                    file_info[file_name] = stave_count
    
    return file_info

def normalize_filename(filename):
    """
    Normalize filenames to handle different formats (with or without extensions, with HEIC suffix)
    """
    # Remove file extension if present
    base_name = os.path.splitext(filename)[0]
    
    # Remove "HEIC" suffix if present (from HEIC conversion)
    if base_name.endswith("HEIC"):
        base_name = base_name[:-4]  # Remove "HEIC" from the end
        
    return base_name

def rename_files(directory_path, file_info):
    """
    Rename files in a directory based on stave count
    """
    # Check if directory exists
    if not os.path.exists(directory_path):
        print(f"Error: Directory {directory_path} does not exist.")
        return
    
    # Get all files in the directory
    try:
        files = os.listdir(directory_path)
    except Exception as e:
        print(f"Error listing files in {directory_path}: {str(e)}")
        return
    
    renamed_count = 0
    not_found_count = 0
    
    for file in files:
        # Skip directories
        if os.path.isdir(os.path.join(directory_path, file)):
            continue
        
        # Get file extension
        file_ext = os.path.splitext(file)[1]
        
        # Normalize filename for comparison
        normalized_name = normalize_filename(file)
        
        # Find matching entry in file_info
        found = False
        for original_name, stave_count in file_info.items():
            # Normalize the original name for comparison
            normalized_original = normalize_filename(original_name)
            
            if normalized_name == normalized_original:
                # Create new filename with stave count
                new_filename = f"{stave_count}{file_ext}"
                
                # Rename the file
                old_path = os.path.join(directory_path, file)
                new_path = os.path.join(directory_path, new_filename)
                
                # Handle case where the target filename already exists
                counter = 1
                while os.path.exists(new_path):
                    new_filename = f"{stave_count}_{counter}{file_ext}"
                    new_path = os.path.join(directory_path, new_filename)
                    counter += 1
                
                try:
                    os.rename(old_path, new_path)
                    print(f"Renamed: {file} -> {new_filename}")
                    renamed_count += 1
                    found = True
                except Exception as e:
                    print(f"Error renaming {file}: {str(e)}")
                break
        
        if not found:
            print(f"No matching stave count found for: {file}")
            not_found_count += 1
    
    print(f"\nSummary: Renamed {renamed_count} files, {not_found_count} files not matched")

def main():
    print("Starting the stave file renamer script...")
    
    # Connect to Google Sheets
    print(f"Authenticating with Google Sheets...")
    try:
        sheet = authenticate_google_sheets(CREDENTIALS_PATH, SHEET_NAME)
    except Exception as e:
        print(f"Error connecting to Google Sheets: {str(e)}")
        return
    
    # Extract file information from sheet
    print("Extracting file names and stave counts from Google Sheet...")
    try:
        file_info = extract_file_info_from_sheet(sheet)
        print(f"Found {len(file_info)} file name to stave count mappings.")
    except Exception as e:
        print(f"Error extracting file info: {str(e)}")
        return
    
    # Save mapping to file
    if file_info:
        print(f"Saving mapping to {OUTPUT_MAPPING_FILE}...")
        try:
            save_mapping_to_file(file_info, OUTPUT_MAPPING_FILE)
        except Exception as e:
            print(f"Error saving mapping: {str(e)}")
            return
    else:
        print("No file information found to save.")
        return
    
    # Rename files
    print(f"Renaming files in {LOCAL_IMAGES_DIRECTORY}...")
    try:
        rename_files(LOCAL_IMAGES_DIRECTORY, file_info)
    except Exception as e:
        print(f"Error during file renaming: {str(e)}")
    
    print("Script completed!")

if __name__ == "__main__":
    main()