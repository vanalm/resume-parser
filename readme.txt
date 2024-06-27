### Project Setup and Run Instructions

#### Step 1: Install Python
Ensure Python 3.x is installed on your system.

#### Step 2: Clone the Project
Download and extract the project folder to your local system.

#### Step 3: Create and Activate a Virtual Environment
# Virtual environments allow you to manage separate package installations for different projects.
Navigate to the project directory in a terminal or command prompt, then create and activate a virtual environment:

For Windows:
python -m venv venv
venv\Scripts\activate

For macOS and Linux:
python3 -m venv venv
source venv/bin/activate

#### Step 4: Install Dependencies
With the virtual environment activated, install the required dependencies:
pip install -r requirements.txt

#### Step 5: Obtain API Credentials
Create an account at Textkernel by navigating to:
https://cloud.textkernel.com/tx/console/register
Once registered, log in and retrieve your API credentials from:
https://cloud.textkernel.com/tx/console/saasaccount

#### Step 6: Setup Environment Variables
Open the .env file in the project directory and fill in the following with your API credentials:
SERVICE_KEY=your_service_key
ACCOUNT_ID=your_account_id
ACCOUNT=your_account_username
PASSWORD=your_account_password

#### Step 7: Add PDF Resumes
Place your PDF resume files in the /resumes/ subdirectory.

#### Step 8: Run the Script
Ensure the virtual environment is activated, then execute the script:
python pdf_resume_parser.py

#### Step 9: Deactivate Virtual Environment
Once done, deactivate the virtual environment:
For Windows:
venv\Scripts\deactivate

For macOS and Linux:
deactivate

#### Output
The extracted data will be saved in a CSV file in the /resumes/ directory. Check this file to view the resume data extracted.
