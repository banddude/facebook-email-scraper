# Facebook Email Scraper

A web application that finds business email addresses from Facebook pages. Upload a CSV file with business names and locations, and get back a CSV with their email addresses.

## Requirements

- Python 3.8 or higher
- Chrome browser installed
- Internet connection

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd FacebookEmailScraper
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the application:
```bash
python app.py
```

2. Open your browser and go to:
```
http://localhost:5001
```

3. Upload a CSV file with the following columns:
   - business_name
   - location

4. Wait for processing to complete
5. Download the results file

## CSV Format

Input CSV format:
```csv
business_name,location
"Business Name 1","City 1"
"Business Name 2","City 2"
```

Output CSV format:
```csv
business_name,location,email
"Business Name 1","City 1","email1@example.com"
"Business Name 2","City 2","email2@example.com"
```

## Features

- Automated email finding from Facebook pages
- Progress tracking
- Handles multiple businesses
- Downloads results as CSV
- Clean web interface

## Notes

- The application uses Chrome in headless mode
- Results are saved in the 'uploads' directory
- Processing time depends on the number of businesses 