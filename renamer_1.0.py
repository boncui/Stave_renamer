import os
import gspread
import logging
import requests
from urllib.parse import urlparse
from oauth2client.service_account import ServiceAccountCredentials

# 🏠 Define Paths
DATA_DIR = "/Users/boncui/Desktop/Projects/Stave Project/Data"  # Main data folder
CREDENTIALS_PATH = "/Users/boncui/Desktop/Projects/Stave Project/Stave_renamer/credentials.json"
SHEET_NAME = "Copy of Independent Stave Company Data Collection (Responses)"

# 📜 Logging Setup
logging.basicConfig(level=logging.INFO, format='%(message)s')

def authenticate_google_sheets(credentials_path, sheet_name):
    """Authenticate and access Google Sheets."""
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scope)
    client = gspread.authorize(creds)
    return client.open(sheet_name).sheet1

def extract_drive_file_id(view_url):
    """Extract the file ID from a Google Drive link."""
    if "drive.google.com" in view_url:
        if "id=" in view_url:
            return view_url.split("id=")[-1]
        elif "/file/d/" in view_url:
            return view_url.split("/file/d/")[1].split("/")[0]
    return None

def get_drive_filename(file_id, credentials_path):
    """Retrieve the actual file name from Google Drive using the file ID."""
    url = f"https://www.googleapis.com/drive/v3/files/{file_id}?fields=name"
    creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, ["https://www.googleapis.com/auth/drive"])
    headers = {"Authorization": f"Bearer {creds.get_access_token().access_token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get("name", file_id)
    return file_id

def fetch_sheet_data(sheet):
    """Retrieve filenames and stave counts from Google Sheets."""
    data = sheet.get_all_records()
    extracted_data = {}
    
    for row in data:
        image_url = str(row.get("Upload Stave Pallet Photo", "")).strip()
        stave_count = str(row.get("Enter Stave Count", "")).strip()
        
        if image_url and stave_count:
            file_id = extract_drive_file_id(image_url)
            if file_id:
                file_name = get_drive_filename(file_id, CREDENTIALS_PATH)  # Fetch actual filename from Drive
                extracted_data[file_name] = stave_count
    
    return extracted_data

def test_fetch_stave_count():
    """Test function to check if stave counts can be accessed with correct filenames."""
    sheet = authenticate_google_sheets(CREDENTIALS_PATH, SHEET_NAME)
    sheet_data = fetch_sheet_data(sheet)
    logging.info("Retrieved Stave Counts with Filenames:")
    for file_name, stave_count in sheet_data.items():
        logging.info(f"{file_name}: {stave_count}")

# 🎯 Run the test
if __name__ == "__main__":
    test_fetch_stave_count()
    logging.info("✅ Stave count retrieval test completed.")