import os
import requests
import pandas as pd
from dotenv import load_dotenv
import base64
from datetime import datetime

# Load environment variables
load_dotenv()

# API and authentication details
API_URL = 'https://api.us.textkernel.com/tx/v10/parser/resume'
ACCOUNT_ID = os.getenv('ACCOUNT_ID')
SERVICE_KEY = os.getenv('SERVICE_KEY')
TARGET_DIRECTORY = os.getenv('TARGET_DIRECTORY')

# Function to encode file to Base64
def encode_file_to_base64(file_path):
    with open(file_path, 'rb') as file:
        return base64.b64encode(file.read()).decode('utf-8')

# Function to send file to API and parse the resume
def parse_resume(file_path):
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Tx-AccountId': ACCOUNT_ID,
        'Tx-ServiceKey': SERVICE_KEY
    }
    data = {
        "DocumentAsBase64String": encode_file_to_base64(file_path),
        "DocumentLastModified": datetime.now().strftime('%Y-%m-%d')  # Default to today's date
    }
    response = requests.post(API_URL, headers=headers, json=data)
    return response.json()

# Function to extract specific fields from parsed data
def extract_fields(parsed_data):
    resume = parsed_data['Value']['ResumeData']
    contact = resume['ContactInformation']
    education = resume['Education']['EducationDetails']
    employment = resume['EmploymentHistory']['Positions']

    extracted_info = {
        'Name': f"{contact['CandidateName']['FamilyName']}-{contact['CandidateName']['GivenName']}",
        'Last Name': contact['CandidateName']['FamilyName'],
        'First Name': contact['CandidateName']['GivenName'],
        'LinkedIn': next((web['Address'] for web in contact['WebAddresses'] if web['Type'] == 'LinkedIn'), None),
        'Phone': contact['Telephones'][0]['Normalized'],
        'City': contact['Location']['Municipality'],
        'State': contact['Location']['Regions'][0],
        'First Degree': education[0]['Degree']['Name']['Normalized'],
        'First Degree Year': education[0]['EndDate']['Date'][:4],
        'First Degree Field': education[0]['Degree']['Type'],
        'First Degree Institution': education[0]['SchoolName']['Normalized'],
        'Most Recent Job Title': employment[0]['JobTitle']['Normalized'],
        'Most Recent Job Company': employment[0]['Employer']['Name']['Normalized'],
        'Most Recent Job Years': f"{employment[0]['StartDate']['Date'][:4]}-{employment[0]['EndDate']['Date'][:4]}"
    }

    return extracted_info

# List to store all parsed and extracted resume data
all_resumes = []

# Iterate over all PDF files in the directory
for filename in os.listdir(TARGET_DIRECTORY):
    if filename.endswith(".pdf"):
        file_path = os.path.join(TARGET_DIRECTORY, filename)
        print(f"Processing {filename}...")
        parsed_data = parse_resume(file_path)
        if 'Value' in parsed_data:  # Ensure there is a 'Value' key in the response
            extracted_data = extract_fields(parsed_data)
            all_resumes.append(extracted_data)
        else:
            print("Error parsing:", parsed_data.get('Message', 'No error message available'))

# Display all extracted data
print("\nExtracted Resume Data:")
print(all_resumes)

# Optionally, convert to DataFrame and save as CSV
df = pd.DataFrame(all_resumes)
csv_path = os.path.join(TARGET_DIRECTORY, 'parsed_resumes.csv')
df.to_csv(csv_path, index=False)
print(f"All results have been concatenated and saved to {csv_path}")
