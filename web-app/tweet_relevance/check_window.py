import pandas as pd
import os
import json
import logging
from sklearn.metrics import accuracy_score, classification_report
import joblib

# Configuration
WINDOW_SIZE = 50  # Minimum data points needed to trigger retraining
METADATA_FILE = '.training_metadata.json'
TRIGGER_FILE = '.trigger_file.txt'

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def should_retrain():
    try:
        logging.info("Reading feedback data...")
        current_data = pd.read_csv('feedback_log.csv')
        current_rows = len(current_data)
        logging.info(f"Total feedback rows: {current_rows}")
    except Exception as e:
        logging.error(f"Failed to read feedback_log.csv: {e}")
        return False, 0

    try:
        if os.path.exists(METADATA_FILE):
            with open(METADATA_FILE, 'r') as f:
                metadata = json.load(f)
            last_trained_rows = metadata.get('last_trained_rows', 0)
            logging.info(f"Last trained on {last_trained_rows} rows")
        else:
            last_trained_rows = 0
            logging.info("No previous training metadata found")
    except Exception as e:
        logging.error(f"Failed to read metadata file: {e}")
        last_trained_rows = 0

    new_rows = current_rows - last_trained_rows
    needs_retraining = new_rows >= WINDOW_SIZE

    try:
        with open(TRIGGER_FILE, 'w') as f:
            f.write(str(int(needs_retraining)))
            f.write(f"\nNew rows since last training: {new_rows}")
            f.write(f"\nWindow size threshold: {WINDOW_SIZE}")
        logging.info(f"Trigger file updated at {TRIGGER_FILE}")
    except Exception as e:
        logging.error(f"Failed to write trigger file: {e}")

    return needs_retraining, new_rows

if __name__ == "__main__":
    needs_retraining, new_rows = should_retrain()
    if needs_retraining:
        logging.info(f"Retraining triggered with {new_rows} new samples")
    else:
        logging.info(f"Not enough data: {new_rows}/{WINDOW_SIZE} required samples")
