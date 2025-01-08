import sys
import os
import csv
import logging
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QPushButton, QFileDialog, QLabel, QProgressBar)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.expanduser('~/Desktop/facebook_scraper.log')),
        logging.StreamHandler()
    ]
)

class ProcessingThread(QThread):
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, csv_file):
        super().__init__()
        self.csv_file = csv_file

    def run(self):
        try:
            logging.debug("Starting ProcessingThread")
            # Initialize Chrome in headless mode
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--no-sandbox')
            
            # Get the chromedriver path
            if getattr(sys, 'frozen', False):
                chromedriver_path = os.path.join(os.path.dirname(sys.executable), 'chromedriver')
                logging.debug(f"Running from PyInstaller bundle, chromedriver path: {chromedriver_path}")
            else:
                chromedriver_path = 'chromedriver'
                logging.debug(f"Running from Python, chromedriver path: {chromedriver_path}")
            
            service = Service(chromedriver_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)

            total_rows = sum(1 for _ in open(self.csv_file)) - 1
            processed = 0

            with open(self.csv_file, 'r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    facebook_url = row.get('facebook_url', '')
                    if facebook_url:
                        try:
                            driver.get(facebook_url)
                            # Add email extraction logic here
                            self.status.emit(f"Processed: {facebook_url}")
                        except Exception as e:
                            logging.error(f"Error processing URL: {str(e)}")
                            self.status.emit(f"Error processing {facebook_url}: {str(e)}")
                    
                    processed += 1
                    progress = int((processed / total_rows) * 100)
                    self.progress.emit(progress)

            driver.quit()
            self.finished.emit()
        except Exception as e:
            logging.error(f"Thread error: {str(e)}")
            self.status.emit(f"Error: {str(e)}")
            self.finished.emit()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        logging.debug("Initializing MainWindow")
        self.setWindowTitle("Facebook Email Scraper")
        self.setFixedSize(800, 400)

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)

        # Create UI elements
        title_label = QLabel("Facebook Email Scraper")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        self.select_button = QPushButton("Select CSV File")
        self.select_button.setFixedSize(200, 40)
        self.select_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 5px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.select_button.clicked.connect(self.select_file)
        layout.addWidget(self.select_button, alignment=Qt.AlignmentFlag.AlignCenter)

        self.status_label = QLabel("Select a CSV file to begin...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("font-size: 14px;")
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(600)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid grey;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
            }
        """)
        layout.addWidget(self.progress_bar, alignment=Qt.AlignmentFlag.AlignCenter)

        # Center the window on the screen
        screen = QApplication.primaryScreen().geometry()
        self.move(
            (screen.width() - self.width()) // 2,
            (screen.height() - self.height()) // 2
        )
        logging.debug("MainWindow initialized")

    def select_file(self):
        logging.debug("Select file button clicked")
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Select CSV File",
            "",
            "CSV Files (*.csv)"
        )
        if file_name:
            logging.debug(f"Selected file: {file_name}")
            self.status_label.setText(f"Processing {os.path.basename(file_name)}...")
            self.select_button.setEnabled(False)
            self.progress_bar.setValue(0)

            self.thread = ProcessingThread(file_name)
            self.thread.progress.connect(self.update_progress)
            self.thread.status.connect(self.update_status)
            self.thread.finished.connect(self.processing_finished)
            self.thread.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def update_status(self, message):
        logging.debug(f"Status update: {message}")
        self.status_label.setText(message)

    def processing_finished(self):
        logging.debug("Processing finished")
        self.select_button.setEnabled(True)
        self.status_label.setText("Processing completed!")

if __name__ == '__main__':
    try:
        logging.debug("Application starting")
        app = QApplication(sys.argv)
        app.setStyle('Fusion')  # Use Fusion style for a modern look
        window = MainWindow()
        window.show()
        logging.debug("Window shown")
        sys.exit(app.exec())
    except Exception as e:
        logging.error(f"Application error: {str(e)}")
        raise 