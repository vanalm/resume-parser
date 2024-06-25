import os
import requests
import pandas as pd
from dotenv import load_dotenv
import base64
from datetime import datetime
from extraction import extract_resume_data
# Load environment variables
load_dotenv()

# API and authentication details
API_URL = 'https://api.us.textkernel.com/tx/v10/parser/resume'
ACCOUNT_ID = os.getenv('ACCOUNT_ID')
SERVICE_KEY = os.getenv('SERVICE_KEY')
# TARGET_DIRECTORY = os.getenv('TARGET_DIRECTORY')
TARGET_DIRECTORY = './resumes'
# target_file = './resumes_test/Ning Xue_CV.pdf'
# DEFINING KEYWORDS FOR EXTRACTION
programming_keywords = {
    "Python": ["python"],
    "C": [" c "],  # difficult to ensure 'C' is not matched in words like 'React'
    "C++": ["c++", "cpp"],
    "Swift": ["swift"],
    # "R": [" r ", " r,"]  # difficult to ensure 'R' is not matched in words like 'programming']
}
professional_keywords = {
    "Neuroscience": ["neuroscience"],
    "Imaging data": ["imaging data", "medical imaging"],
    "Bioinformatics": ["bioinformatics"]
}


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



# List to store all parsed and extracted resume data

all_resumes = []

# Iterate over all PDF files in the directory
for filename in os.listdir(TARGET_DIRECTORY):
    if filename.endswith(".pdf"):
        file_path = os.path.join(TARGET_DIRECTORY, filename)
        # file_path = target_file
        print(f"Processing {filename}...")
        parsed_data = parse_resume(file_path)
        # print(f"\n\nRESUME DATA\n\n{parsed_data}")
        if 'Value' in parsed_data:  # Ensure there is a 'Value' key in the response
            extracted_data = extract_resume_data(parsed_data, programming_keywords, professional_keywords)

            # extracted_data = extract_resume_data(parsed_data)
            if extracted_data:
                all_resumes.append(extracted_data)
            else:
                print(f"Failed to extract data for {filename}")
        else:
            print(f"Error parsing {filename}: {parsed_data.get('Message', 'No error message available')}")

# Display all extracted data
print("\nExtracted Resume Data:")
print(all_resumes)

# Optionally, convert to DataFrame and save as CSV
df = pd.DataFrame(all_resumes)
csv_path = os.path.join(TARGET_DIRECTORY, 'parsed_resumes.csv')
df.to_csv(csv_path, index=False)
print(f"All results have been concatenated")

