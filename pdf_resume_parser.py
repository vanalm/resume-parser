import os
import glob
import json
import csv
import requests
import pandas as pd
from dotenv import load_dotenv
import base64
from datetime import datetime
from areacode_mapper import get_city_and_state_from_area_code
from tqdm import tqdm

# Load environment variables
load_dotenv()
csv_file_name = 'resume_data.csv'
directory_path =  "./missing_resumes_test"

# API and authentication details
API_URL = 'https://api.us.textkernel.com/tx/v10/parser/resume'
ACCOUNT_ID = os.getenv('ACCOUNT_ID')
SERVICE_KEY = os.getenv('SERVICE_KEY')

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
def extract_fields_from_json(data, resume_filename):
    contact_info = data['Value']['ResumeData']['ContactInformation']
    education_info = data['Value']['ResumeData']['Education']
    employment_info = data['Value']['ResumeData']['EmploymentHistory']
    skills_info = data['Value']['ResumeData']['Skills']['Raw']
    summary_info = data['Value']['ResumeData'].get('ProfessionalSummary', '')

    # Prepare education details
    education_details = education_info.get('EducationDetails', [])
    education_details_sorted = sorted(
        education_details, key=lambda x: x.get('EndDate', {}).get('Date', '') if x.get('EndDate') else ''
    ) if education_details else []

    # Prepare employment details
    positions = employment_info.get('Positions', [])
    positions_sorted = sorted(
        positions, key=lambda x: x.get('StartDate', {}).get('Date', '') if x.get('StartDate') else '', reverse=True
    ) if positions else []

    # Normalize and extract skills
    skill_names = {skill['Name'].lower() for skill in skills_info}

    fields = {
        'Name in special format': f"{contact_info['CandidateName'].get('FamilyName', '')}-{contact_info['CandidateName'].get('GivenName', '')}-{contact_info['CandidateName'].get('MiddleName', '')}",
        'last name': contact_info['CandidateName'].get('FamilyName', ''),
        'first name': contact_info['CandidateName'].get('GivenName', ''),
        'original resume filename': resume_filename,
        'LinkedIn address': contact_info.get('WebAddresses', [{}])[0].get('Address', ''),
        'Self-made title': summary_info,
        'phone': contact_info.get('Telephones', [{}])[0].get('Normalized', ''),
        'areacode location': get_city_and_state_from_area_code(contact_info.get('Telephones', [{}])[0].get('AreaCityCode', '')),
        'current city': contact_info.get('Address', {}).get('City', ''),
        'current state': contact_info.get('Address', {}).get('Region', ''),
        'earliest degree typically Bachelors degree': education_details_sorted[0].get('Degree', {}).get('Name', {}).get('Raw', '') if education_details_sorted else '',
        'earliest degree year': education_details_sorted[0].get('EndDate', {}).get('Date', '')[:4] if education_details_sorted and education_details_sorted[0].get('EndDate') else '',
        'earliest degree field': ', '.join(education_details_sorted[0].get('Majors', [])) if education_details_sorted else '',
        'earliest degree institution': education_details_sorted[0].get('SchoolName', {}).get('Normalized', '') if education_details_sorted else '',
        'second degree typically masters degree': education_details_sorted[1].get('Degree', {}).get('Name', {}).get('Raw', '') if len(education_details_sorted) > 1 else '',
        'second degree year': education_details_sorted[1].get('EndDate', {}).get('Date', '')[:4] if len(education_details_sorted) > 1 and education_details_sorted[1].get('EndDate') else '',
        'second degree field': ', '.join(education_details_sorted[1].get('Majors', [])) if len(education_details_sorted) > 1 else '',
        'second degree institution': education_details_sorted[1].get('SchoolName', {}).get('Normalized', '') if len(education_details_sorted) > 1 else '',
        'third degree typically PhD or doctor of philosophy or other doctoral level': education_details_sorted[2].get('Degree', {}).get('Name', {}).get('Raw', '') if len(education_details_sorted) > 2 else '',
        'third degree year': education_details_sorted[2].get('EndDate', {}).get('Date', '')[:4] if len(education_details_sorted) > 2 and education_details_sorted[2].get('EndDate') else '',
        'third degree field': ', '.join(education_details_sorted[2].get('Majors', [])) if len(education_details_sorted) > 2 else '',
        'third degree institution': education_details_sorted[2].get('SchoolName', {}).get('Normalized', '') if len(education_details_sorted) > 2 else '',
        'other degrees': 'y' if len(education_details_sorted) > 3 else 'n',
        'most recent job title': positions_sorted[0].get('JobTitle', {}).get('Raw', '') if positions_sorted else '',
        'most recent job company': positions_sorted[0].get('Employer', {}).get('Name', {}).get('Normalized', '') if positions_sorted else '',
        'most recent job years': positions_sorted[0].get('StartDate', {}).get('Date', '')[:4] + '-' + (positions_sorted[0].get('EndDate', {}).get('Date', '')[:4] if not positions_sorted[0].get('IsCurrent', False) and positions_sorted[0].get('EndDate') else 'Present') if positions_sorted else '',
        'previous job title': positions_sorted[1].get('JobTitle', {}).get('Raw', '') if len(positions_sorted) > 1 else '',
        'previous job company': positions_sorted[1].get('Employer', {}).get('Name', {}).get('Normalized', '') if len(positions_sorted) > 1 else '',
        'previous job years': positions_sorted[1].get('StartDate', {}).get('Date', '')[:4] + '-' + (positions_sorted[1].get('EndDate', {}).get('Date', '')[:4] if not positions_sorted[1].get('IsCurrent', False) and positions_sorted[1].get('EndDate') else 'Present') if len(positions_sorted) > 1 else '',
        'next previous job title': positions_sorted[2].get('JobTitle', {}).get('Raw', '') if len(positions_sorted) > 2 else '',
        'next previous job company': positions_sorted[2].get('Employer', {}).get('Name', {}).get('Normalized', '') if len(positions_sorted) > 2 else '',
        'next previous job years': positions_sorted[2].get('StartDate', {}).get('Date', '')[:4] + '-' + (positions_sorted[2].get('EndDate', {}).get('Date', '')[:4] if not positions_sorted[2].get('IsCurrent', False) and positions_sorted[2].get('EndDate') else 'Present') if len(positions_sorted) > 2 else '',
        '2nd next previous job title': positions_sorted[3].get('JobTitle', {}).get('Raw', '') if len(positions_sorted) > 3 else '',
        '2nd next previous job company': positions_sorted[3].get('Employer', {}).get('Name', {}).get('Normalized', '') if len(positions_sorted) > 3 else '',
        '2nd next previous job years': positions_sorted[3].get('StartDate', {}).get('Date', '')[:4] + '-' + (positions_sorted[3].get('EndDate', {}).get('Date', '')[:4] if not positions_sorted[3].get('IsCurrent', False) and positions_sorted[3].get('EndDate') else 'Present') if len(positions_sorted) > 3 else '',
        'Python experience': 'y' if 'python' in skill_names else 'n',
        'C programming language experience': 'y' if 'c' in skill_names else 'n',
        'C++ programming experience': 'y' if 'c++' in skill_names else 'n',
        'Swift programming experience': 'y' if 'swift' in skill_names else 'n',
        'R programming experience': 'y' if 'r' in skill_names else 'n',
        'Neuroscience professional experience': 'y' if 'neuroscience' in skill_names else 'n',
        'Imaging data professional experience': 'y' if 'imaging data' in skill_names else 'n',
        'Bioinformatics professional experience': 'y' if 'bioinformatics' in skill_names else 'n'
    }

    return fields

#### the following function is deprecated and replaced by the above function to accommodate different date formats ###

# def extract_fields_from_json(data, resume_filename):
#     contact_info = data['Value']['ResumeData']['ContactInformation']
#     education_info = data['Value']['ResumeData']['Education']
#     employment_info = data['Value']['ResumeData']['EmploymentHistory']
#     skills_info = data['Value']['ResumeData']['Skills']['Raw']
#     summary_info = data['Value']['ResumeData'].get('ProfessionalSummary', '')

#     # Prepare education details
#     education_details = education_info.get('EducationDetails', [])
#     education_details_sorted = sorted(education_details, key=lambda x: x['EndDate']['Date']) if education_details else []

#     # Prepare employment details
#     positions = employment_info.get('Positions', [])
#     positions_sorted = sorted(positions, key=lambda x: x['StartDate']['Date'], reverse=True) if positions else []

#     # Normalize and extract skills
#     skill_names = {skill['Name'].lower() for skill in skills_info}

#     fields = {
#         'Name in special format': f"{contact_info['CandidateName'].get('FamilyName', '')}-{contact_info['CandidateName'].get('GivenName', '')}-{contact_info['CandidateName'].get('MiddleName', '')}",
#         'last name': contact_info['CandidateName'].get('FamilyName', ''),
#         'first name': contact_info['CandidateName'].get('GivenName', ''),
#         'original resume filename': resume_filename,
#         'LinkedIn address': contact_info.get('WebAddresses', [{}])[0].get('Address', ''),
#         'Self-made title': summary_info,
#         'phone': contact_info.get('Telephones', [{}])[0].get('Normalized', ''),
#         'areacode location': get_city_and_state_from_area_code(contact_info.get('Telephones', [{}])[0].get('AreaCityCode', '')),
#         'current city': contact_info.get('Address', {}).get('City', ''),
#         'current state': contact_info.get('Address', {}).get('Region', ''),
#         'earliest degree typically Bachelors degree': education_details_sorted[0].get('Degree', {}).get('Name', {}).get('Raw', '') if education_details_sorted else '',
#         'earliest degree year': education_details_sorted[0].get('EndDate', {}).get('Date', '')[:4] if education_details_sorted else '',
#         'earliest degree field': ', '.join(education_details_sorted[0].get('Majors', [])) if education_details_sorted else '',
#         'earliest degree institution': education_details_sorted[0].get('SchoolName', {}).get('Normalized', '') if education_details_sorted else '',
#         'second degree typically masters degree': education_details_sorted[1].get('Degree', {}).get('Name', {}).get('Raw', '') if len(education_details_sorted) > 1 else '',
#         'second degree year': education_details_sorted[1].get('EndDate', {}).get('Date', '')[:4] if len(education_details_sorted) > 1 else '',
#         'second degree field': ', '.join(education_details_sorted[1].get('Majors', [])) if len(education_details_sorted) > 1 else '',
#         'second degree institution': education_details_sorted[1].get('SchoolName', {}).get('Normalized', '') if len(education_details_sorted) > 1 else '',
#         'third degree typically PhD or doctor of philosophy or other doctoral level': education_details_sorted[2].get('Degree', {}).get('Name', {}).get('Raw', '') if len(education_details_sorted) > 2 else '',
#         'third degree year': education_details_sorted[2].get('EndDate', {}).get('Date', '')[:4] if len(education_details_sorted) > 2 else '',
#         'third degree field': ', '.join(education_details_sorted[2].get('Majors', [])) if len(education_details_sorted) > 2 else '',
#         'third degree institution': education_details_sorted[2].get('SchoolName', {}).get('Normalized', '') if len(education_details_sorted) > 2 else '',
#         'other degrees': 'y' if len(education_details_sorted) > 3 else 'n',
#         'most recent job title': positions_sorted[0].get('JobTitle', {}).get('Raw', '') if positions_sorted else '',
#         'most recent job company': positions_sorted[0].get('Employer', {}).get('Name', {}).get('Normalized', '') if positions_sorted else '',
#         'most recent job years': positions_sorted[0].get('StartDate', {}).get('Date', '')[:4] + '-' + (positions_sorted[0].get('EndDate', {}).get('Date', '')[:4] if not positions_sorted[0].get('IsCurrent', False) else 'Present') if positions_sorted else '',
#         'previous job title': positions_sorted[1].get('JobTitle', {}).get('Raw', '') if len(positions_sorted) > 1 else '',
#         'previous job company': positions_sorted[1].get('Employer', {}).get('Name', {}).get('Normalized', '') if len(positions_sorted) > 1 else '',
#         'previous job years': positions_sorted[1].get('StartDate', {}).get('Date', '')[:4] + '-' + (positions_sorted[1].get('EndDate', {}).get('Date', '')[:4] if not positions_sorted[1].get('IsCurrent', False) else 'Present') if len(positions_sorted) > 1 else '',
#         'next previous job title': positions_sorted[2].get('JobTitle', {}).get('Raw', '') if len(positions_sorted) > 2 else '',
#         'next previous job company': positions_sorted[2].get('Employer', {}).get('Name', {}).get('Normalized', '') if len(positions_sorted) > 2 else '',
#         'next previous job years': positions_sorted[2].get('StartDate', {}).get('Date', '')[:4] + '-' + (positions_sorted[2].get('EndDate', {}).get('Date', '')[:4] if not positions_sorted[2].get('IsCurrent', False) else 'Present') if len(positions_sorted) > 2 else '',
#         '2nd next previous job title': positions_sorted[3].get('JobTitle', {}).get('Raw', '') if len(positions_sorted) > 3 else '',
#         '2nd next previous job company': positions_sorted[3].get('Employer', {}).get('Name', {}).get('Normalized', '') if len(positions_sorted) > 3 else '',
#         '2nd next previous job years': positions_sorted[3].get('StartDate', {}).get('Date', '')[:4] + '-' + (positions_sorted[3].get('EndDate', {}).get('Date', '')[:4] if not positions_sorted[3].get('IsCurrent', False) else 'Present') if len(positions_sorted) > 3 else '',
#         'Python experience': 'y' if 'python' in skill_names else 'n',
#         'C programming language experience': 'y' if 'c' in skill_names else 'n',
#         'C++ programming experience': 'y' if 'c++' in skill_names else 'n',
#         'Swift programming experience': 'y' if 'swift' in skill_names else 'n',
#         'R programming experience': 'y' if 'r' in skill_names else 'n',
#         'Neuroscience professional experience': 'y' if 'neuroscience' in skill_names else 'n',
#         'Imaging data professional experience': 'y' if 'imaging data' in skill_names else 'n',
#         'Bioinformatics professional experience': 'y' if 'bioinformatics' in skill_names else 'n'
#     }

#     return fields

# Function to process all PDF files in the given directory
# List to store all parsed and extracted resume data
all_fields = []
# Function to process all PDF files in the given directory
def process_pdfs(directory):
    print(f"Processing PDF files in {directory}")
    pdf_files = glob.glob(os.path.join(directory, "*.pdf"))
    print(f"Found {len(pdf_files)} PDF files in the directory")
    for pdf_file in tqdm(pdf_files, desc="Processing PDFs"):
        try:
            data = parse_resume(pdf_file)
            fields = extract_fields_from_json(data, os.path.basename(pdf_file))
            all_fields.append(fields)
        except Exception as e:
            print(f"Error processing {pdf_file}: {e}")

    # Write all fields to CSV
    if all_fields:
        with open(csv_file_name, mode='w', newline='') as file:
            writer = csv.writer(file)
            # Write header
            writer.writerow(all_fields[0].keys())
            # Write data
            for fields in all_fields:
                writer.writerow(fields.values())

    print(f'{csv_file_name} successfully created!')
    return all_fields

# Provide the path to the directory containing PDF files
all_fields = process_pdfs(directory_path)  # Call the function and store the result

# Optionally, convert to DataFrame and save as CSV
df = pd.DataFrame(all_fields)
# csv_path = os.path.join("directory_path", csv_file_name)

df.to_csv(index=False)
print(f"All results have been concatenated and saved to current directory as {csv_file_name}")
