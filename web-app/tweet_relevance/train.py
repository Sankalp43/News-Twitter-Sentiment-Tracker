# tweet_relevance/model/train.py

import os
import joblib
import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from preprocessing import prepare_data

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

MODEL_DIR = "model/"
os.makedirs(MODEL_DIR, exist_ok=True)

def combine_text(row):
    """
    Combine headline and tweet into one string.
    """
    return row["headline"] + " [SEP] " + row["tweet"]

def train_model():
    try:
        logging.info("Loading and preparing data...")
        X_train, X_test, y_train, y_test = prepare_data("data/initial_dataset/initial_relevance_dataset.csv")
    except Exception as e:
        logging.error(f"Error loading data: {e}")
        return

    try:
        logging.info("Combining headline and tweet text...")
        X_train_combined = X_train.apply(combine_text, axis=1)
        X_test_combined = X_test.apply(combine_text, axis=1)

        logging.info("Vectorizing text with TfidfVectorizer...")
        vectorizer = TfidfVectorizer(max_features=5000)
        X_train_vec = vectorizer.fit_transform(X_train_combined)
        X_test_vec = vectorizer.transform(X_test_combined)

        logging.info("Training Logistic Regression classifier...")
        clf = LogisticRegression(class_weight="balanced", max_iter=1000, random_state=42)
        clf.fit(X_train_vec, y_train)

        logging.info("Evaluating model...")
        y_pred = clf.predict(X_test_vec)
        logging.info("Classification Report:\n" + classification_report(y_test, y_pred))

        logging.info("Saving model and vectorizer...")
        joblib.dump(clf, os.path.join(MODEL_DIR, "relevance_model.joblib"))
        joblib.dump(vectorizer, os.path.join(MODEL_DIR, "vectorizer.joblib"))
        logging.info(f"Saved model and vectorizer to {MODEL_DIR}")
    except Exception as e:
        logging.error(f"Training or saving failed: {e}")

if __name__ == "__main__":
    train_model()
