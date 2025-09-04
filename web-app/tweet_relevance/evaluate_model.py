import os
import pandas as pd
import joblib
import json
from sklearn.metrics import accuracy_score, classification_report
from dvclive import Live

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "model")

def evaluate_performance():
    # Load model and vectorizer
    model = joblib.load(os.path.join(MODEL_DIR, "relevance_model.joblib"))
    vectorizer = joblib.load(os.path.join(MODEL_DIR, "vectorizer.joblib"))
    
    # Load test data (use last 20% of the data as test set)
    data = pd.read_csv('feedback_log.csv')
    test_size = max(1, int(len(data) * 0.2))
    test_data = data.tail(test_size)
    
    # Make predictions - combine headline and tweet as in feedback_trainer.py
    combined_texts = (test_data["headline"] + " [SEP] " + test_data["tweet"]).tolist()
    X_test = vectorizer.transform(combined_texts)
    y_test = test_data["user_label"]  # Using user_label as in feedback_trainer.py
    y_pred = model.predict(X_test)
    
    # Calculate metrics
    accuracy = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, output_dict=True)
    
    # Save metrics
    metrics = {
        'accuracy': float(accuracy),
        'precision': float(report['weighted avg']['precision']),
        'recall': float(report['weighted avg']['recall']),
        'f1_score': float(report['weighted avg']['f1-score'])
    }
    
    # Save metrics with DVC Live
    with Live("metrics") as live:
        for name, value in metrics.items():
            live.log_metric(name, value)
    
    # Update training metadata
    with open('.training_metadata.json', 'w') as f:
        json.dump({
            'last_trained_rows': len(data),
            'last_training_time': pd.Timestamp.now().isoformat(),
            'metrics': metrics
        }, f)
    
    print(f"Model evaluation: Accuracy = {accuracy:.4f}")
    
    return metrics

if __name__ == "__main__":
    evaluate_performance()
