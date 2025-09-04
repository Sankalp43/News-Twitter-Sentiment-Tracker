# tweet_relevance/model/feedback_trainer.py

import os
import joblib
import pandas as pd
import logging
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "model")

def check_if_training_needed():
    try:
        with open('.trigger_file.txt', 'r') as f:
            lines = f.readlines()
            return int(lines[0].strip()) == 1
    except Exception as e:
        logging.error(f"Error reading trigger file: {e}")
        return False

def retrain_model(feedback_data_path):
    """
    Retrain the relevance model using new feedback data.
    """
    try:
        logging.info("Loading feedback data...")
        df = pd.read_csv(feedback_data_path)
    except Exception as e:
        logging.error(f"Failed to load feedback data: {e}")
        return

    try:
        logging.info("Combining headline and tweet...")
        combined_texts = (df["headline"] + " [SEP] " + df["tweet"]).tolist()
        labels = df["user_label"].tolist()

        logging.info("Vectorizing text...")
        vectorizer = TfidfVectorizer(max_features=5000)
        X = vectorizer.fit_transform(combined_texts)

        logging.info("Training new logistic regression model...")
        clf = LogisticRegression(max_iter=500)
        clf.fit(X, labels)

        os.makedirs(MODEL_DIR, exist_ok=True)
        joblib.dump(clf, os.path.join(MODEL_DIR, "relevance_model.joblib"))
        joblib.dump(vectorizer, os.path.join(MODEL_DIR, "vectorizer.joblib"))

        logging.info(f"Model retrained and saved to {MODEL_DIR}")
    except Exception as e:
        logging.error(f"Error during retraining: {e}")

if __name__ == "__main__":
    if not check_if_training_needed():
        logging.info("Training skipped - not enough new data")
        exit(0)

    retrain_model("feedback_log.csv")
