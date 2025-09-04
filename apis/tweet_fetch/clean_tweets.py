import re

def clean_tweet(tweet):
    tweet = tweet.replace('\n', ' ').replace('\r', ' ')
    tweet = tweet.replace("\\'", "'")
    tweet = tweet.replace('’', "'").replace('‘', "'")
    tweet = tweet.replace('“', '"').replace('”', '"')
    tweet = tweet.lower()
    tweet = re.sub(r'https?://\S+|www\.\S+', '', tweet)
    tweet = re.sub(r'@\w+', '', tweet)
    tweet = re.sub(r'#', '', tweet)
    tweet = re.sub(r'[^\x00-\x7F\'-]+', '', tweet)
    tweet = re.sub(r'<.*?>', '', tweet)
    tweet = re.sub(r'\s+', ' ', tweet).strip()
    return tweet

def filter_low_info_tweets(tweets, min_words=5, min_chars=20):
    return [tweet for tweet in tweets if len(tweet.split()) >= min_words and len(tweet) >= min_chars]


def preprocess_tweets(tweets):
    cleaned = [clean_tweet(tweet) for tweet in tweets]
    return filter_low_info_tweets(cleaned)