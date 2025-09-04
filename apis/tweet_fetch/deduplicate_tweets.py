from sentence_transformers import SentenceTransformer
from sklearn.cluster import DBSCAN


def semantic_deduplicate(tweets, eps=0.25, model_name='all-MiniLM-L6-v2'):
    model = SentenceTransformer(model_name)
    embeddings = model.encode(tweets, convert_to_numpy=True, show_progress_bar=True)
    clustering = DBSCAN(eps=eps, min_samples=1, metric='cosine').fit(embeddings)

    unique_tweets = []
    seen_clusters = set()
    for idx, label in enumerate(clustering.labels_):
        if label not in seen_clusters:
            seen_clusters.add(label)
            unique_tweets.append(tweets[idx])
    return unique_tweets