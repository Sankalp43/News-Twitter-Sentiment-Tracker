# main.py
from fastapi import FastAPI
from tweet_fetch.get_tweets_api import app as twitter_app
from news_summary.news_summary_api import app as news_app


main_app = FastAPI()

# Mount sub-applications
main_app.mount("/twitter", twitter_app)
main_app.mount("/news", news_app)

@main_app.get("/")
def root():
    return {"message": "Combined API Server"}
