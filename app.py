from flask import Flask, render_template, request, send_file, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
import threading
import time
import re
import os
import csv
from io import StringIO
from datetime import datetime

app = Flask(__name__)

# Global variable to track processing status
processing_status = {
    'is_processing': False,
    'total_businesses': 0,
    'processed_businesses': 0,
    'current_business': '',
    'output_file': None,
    'error': None
}

class FacebookEmailScraper:
    def __init__(self):
        self.options = webdriver.ChromeOptions()
        self.options.add_argument('--headless')
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-dev-shm-usage')
        
        from webdriver_manager.chrome import ChromeDriverManager
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=self.options)
        self.wait = WebDriverWait(self.driver, 10)

    def search_facebook_page(self, search_term):
        try:
            print(f"Searching for: {search_term}")
            self.driver.get('https://www.google.com')
            time.sleep(2)
            
            search_box = self.wait.until(
                EC.presence_of_element_located((By.NAME, 'q'))
            )
            search_box.clear()
            search_box.send_keys(f"{search_term} facebook")
            search_box.send_keys(Keys.RETURN)
            
            time.sleep(2)
            facebook_link = self.wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//a[contains(@href, 'facebook.com')]")
                )
            )
            url = facebook_link.get_attribute('href')
            print(f"Found Facebook URL: {url}")
            return url
        except Exception as e:
            print(f"Error searching for {search_term}: {str(e)}")
            return None

    def extract_email(self, facebook_url):
        try:
            print(f"Extracting email from: {facebook_url}")
            self.driver.get(facebook_url)
            time.sleep(3)
            
            # Get the main page source
            page_source = self.driver.page_source
            
            # Try to find and click the About link
            try:
                about_link = self.driver.find_element(By.XPATH, "//a[contains(@href, '/about')]")
                about_link.click()
                time.sleep(2)
                page_source += self.driver.page_source
            except:
                pass
                
            # Look for email patterns
            email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
            emails = re.findall(email_pattern, page_source)
            
            # Filter out Facebook emails
            filtered_emails = [
                email for email in emails 
                if not any(domain in email.lower() 
                          for domain in ['facebook.com', 'fb.com'])
            ]
            
            if filtered_emails:
                result = filtered_emails[0]
                print(f"Found email: {result}")
                return result
            
            print("No email found")
            return None
            
        except Exception as e:
            print(f"Error extracting email: {str(e)}")
            return None

    def scrape_email(self, business_name, location):
        try:
            search_term = f"{business_name} {location}"
            facebook_url = self.search_facebook_page(search_term)
            if facebook_url:
                return self.extract_email(facebook_url)
            return None
        except Exception as e:
            print(f"Error in scrape_email: {str(e)}")
            return None

    def close(self):
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass

def process_csv_data(csv_data):
    global processing_status
    
    try:
        print("Starting CSV processing")
        # Create uploads directory if it doesn't exist
        if not os.path.exists('uploads'):
            os.makedirs('uploads')
            
        # Create output file in uploads directory
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join('uploads', f'results_{timestamp}.csv')
        processing_status['output_file'] = output_file
        print(f"Output file will be: {output_file}")
        
        # Read CSV data
        csv_file = StringIO(csv_data.decode('utf-8'))
        businesses = list(csv.DictReader(csv_file))
        processing_status['total_businesses'] = len(businesses)
        print(f"Found {len(businesses)} businesses to process")
        
        # Process businesses
        scraper = None
        try:
            print("Initializing scraper...")
            scraper = FacebookEmailScraper()
            print("Scraper initialized successfully")
            
            with open(output_file, 'w', newline='') as outfile:
                writer = csv.DictWriter(outfile, fieldnames=['business_name', 'location', 'email'])
                writer.writeheader()
                
                for row in businesses:
                    try:
                        print(f"\nProcessing business: {row['business_name']}")
                        processing_status['current_business'] = row['business_name']
                        email = scraper.scrape_email(row['business_name'], row['location'])
                        row['email'] = email if email else 'Not found'
                        writer.writerow(row)
                        processing_status['processed_businesses'] += 1
                        print(f"Completed processing {row['business_name']}")
                    except Exception as e:
                        print(f"Error processing {row['business_name']}: {str(e)}")
                        row['email'] = 'Error during processing'
                        writer.writerow(row)
                        processing_status['processed_businesses'] += 1
        finally:
            if scraper:
                print("Closing scraper...")
                scraper.close()
                print("Scraper closed")
            
    except Exception as e:
        error_msg = f"Error during processing: {str(e)}"
        print(error_msg)
        processing_status['error'] = error_msg
    finally:
        processing_status['is_processing'] = False
        print("Processing completed")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    global processing_status
    
    if processing_status['is_processing']:
        return jsonify({'error': 'Already processing a file'}), 400
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
        
    file = request.files['file']
    if file.filename == '' or not file.filename.endswith('.csv'):
        return jsonify({'error': 'Invalid file'}), 400
    
    try:
        processing_status.update({
            'is_processing': True,
            'total_businesses': 0,
            'processed_businesses': 0,
            'current_business': '',
            'output_file': None,
            'error': None
        })
        
        csv_data = file.read()
        thread = threading.Thread(target=process_csv_data, args=(csv_data,))
        thread.start()
        
        return jsonify({'message': 'Processing started'})
        
    except Exception as e:
        processing_status['is_processing'] = False
        return jsonify({'error': str(e)}), 500

@app.route('/status')
def get_status():
    return jsonify({
        'is_processing': processing_status['is_processing'],
        'total_businesses': processing_status['total_businesses'],
        'processed_businesses': processing_status['processed_businesses'],
        'current_business': processing_status['current_business'],
        'error': processing_status['error'],
        'progress': (processing_status['processed_businesses'] / processing_status['total_businesses'] * 100) 
            if processing_status['total_businesses'] > 0 else 0
    })

@app.route('/download')
def download_file():
    if not processing_status['output_file'] or not os.path.exists(processing_status['output_file']):
        return jsonify({'error': 'No processed file available'}), 404
        
    try:
        # Get the absolute path of the file
        file_path = os.path.abspath(processing_status['output_file'])
        directory = os.path.dirname(file_path)
        filename = os.path.basename(file_path)
        
        # Make sure the directory exists
        if not os.path.exists(directory):
            os.makedirs(directory)
            
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        print(f"Error during download: {str(e)}")
        return jsonify({'error': 'Error downloading file'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001) 