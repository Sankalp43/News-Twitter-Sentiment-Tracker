# tweet_relevance/utils/preprocessing.py

import pandas as pd
from sklearn.model_selection import train_test_split

def load_data(csv_path):
    """
    Load the processed relevance CSV dataset.
    Columns expected: 'headline', 'tweet', 'label'
    """
    df = pd.read_csv(csv_path)
    return df

def prepare_data(csv_path, test_size=0.2, random_state=42):
    """
    Load data and split into train/test sets.
    Returns: X_train, X_test, y_train, y_test
    """
    df = load_data(csv_path)
    X = df[["headline", "tweet"]]
    y = df["label"]
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, stratify=y, random_state=random_state
    )
    
    return X_train, X_test, y_train, y_test

# if __name__ == "__main__":
#     # Example usage
#     X_train, X_test, y_train, y_test = prepare_data("../data/processed/processed_relevance_data.csv")
#     print(f"Train size: {len(X_train)}, Test size: {len(X_test)}")
