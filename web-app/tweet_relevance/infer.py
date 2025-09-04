# tweet_relevance/model/infer.py

import os
import joblib


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "model")

def load_model_and_vectorizer():
    clf = joblib.load(os.path.join(MODEL_DIR, "relevance_model.joblib"))
    vectorizer = joblib.load(os.path.join(MODEL_DIR, "vectorizer.joblib"))
    return clf, vectorizer

def predict_relevance(headline, tweet):
    """
    Predict relevance of a tweet to a headline.
    """
    clf, vectorizer = load_model_and_vectorizer()
    combined_text = headline + " [SEP] " + tweet
    X = vectorizer.transform([combined_text])

    pred = clf.predict(X)[0]
    proba = clf.predict_proba(X)[0][pred]

    return {
        "relevant": bool(pred),
        "confidence": round(proba, 3)
    }
