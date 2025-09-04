# API Server (FastAPI)
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
import asyncio
from .fetch_tweets import load_client, fetch_tweets
from .clean_tweets import preprocess_tweets
from .deduplicate_tweets import semantic_deduplicate
# from sentiment_theme import analyze_sentiments_and_themes
from .summarize_analysis import summarize_tweets
from httpx import HTTPError
from httpx import HTTPStatusError, RequestError

app = FastAPI()

class TweetRequest(BaseModel):
    title: str
    max_tweets: int = 20

async def process_tweets(client, title, max_tweets):
    # 1. Fetch tweets (with built-in delays)
    raw_tweets = await fetch_tweets(client, title, max_tweets)
    
    # 2. Post-processing pipeline
    cleaned = preprocess_tweets(raw_tweets[0])  # Your existing logic
    unique = semantic_deduplicate(cleaned)
    summary = summarize_tweets(unique, title)
    
    # 3. Return structured response
    return {
        "cleaned_tweets": cleaned,
        "raw_stats": {
            "likes": raw_tweets[1],
            "replies": raw_tweets[2],
            "retweets": raw_tweets[3]
        },
        "summary": summary
    }

@app.post("/tweets")
async def get_processed_tweets(request: TweetRequest):
    client = load_client()  # Reuse authenticated client

    try:
        return await process_tweets(client, request.title, request.max_tweets)
    except HTTPError as e:
        if e.response.status_code == 429:
            # Option 1: Return a 429 error with a message
            raise HTTPStatusError(status_code=429, detail="Rate limit exceeded. Please try again later.")
        elif e.response.status_code == 404:
            # Option 2: Return a 404 error with a message
            raise HTTPStatusError(status_code=404, detail=f"No tweets found for '{request.title}'")
        else:
            # Option 3: Return a generic error message
            raise HTTPStatusError(status_code=500, detail="An unexpected error occurred.")
        # Option 1: Return a 404 error with a message
    #     raise HTTPException(status_code=404, detail=f"No tweets found for '{request.title}'")
    # return await process_tweets(client, request.title, request.max_tweets)
