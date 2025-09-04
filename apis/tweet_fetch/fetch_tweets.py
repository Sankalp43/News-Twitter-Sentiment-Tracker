### fetch_tweets.py
import asyncio
import random
from twikit import Client, TooManyRequests
from pathlib import Path
import logging
MAX_TWEETS = 100
SLEEP_RANGE = (5, 15)
import time
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry_if_exception_type
from httpx import HTTPError
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("twikit").setLevel(logging.WARNING)
# Set up logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

client = Client(language='en-US')

def load_client():
    script_dir = Path(__file__).resolve().parent
    cookies_path = script_dir / 'cookies.json'
    try:
        client.load_cookies(cookies_path)
    except FileNotFoundError:
        raise Exception("Login required. Please login manually once to save cookies.")
    return client

@retry(
    wait=wait_exponential(multiplier=1, min=4, max=60),
    stop=stop_after_attempt(5),
    retry=(retry_if_exception_type(TooManyRequests))
)
async def fetch_tweets(client, QUERY, MAX_TWEETS):
    collected = []
    attempts = 0

    try:
        result = await client.search_tweet(query=QUERY, product='Top')
    except (TooManyRequests, HTTPError) as e:
            if e.status_code == 429:
                # print("Rate limit exceeded. Waiting 60 seconds...")
                # logging.info("Rate limit exceeded. Waiting 60 seconds...")  
                reset_time = int(result.headers.get('x-rate-limit-reset', 60))
                logging.info(f"Rate limit exceeded. Waiting until {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(reset_time))}...")
                # Calculate the time to wait until the rate limit resets
                logging.info(f"Rate limit reset time: {int(result.headers.get('x-rate-limit-reset', time.time() + 60))}")
                await asyncio.sleep(reset_time - time.time() + 1)
                attempts += 1
            
            if e.status_code == 404:
                logging.warning(f"404 on {QUERY}, retrying...")
                await asyncio.sleep(5)
            #     continue
            # raise
    collected.extend(result)
    # print(f"Initial batch: {len(result)} tweets")
    logging.info(f"Initial batch: {len(result)} tweets")

    while len(collected) < MAX_TWEETS and attempts < 10:
        time_sleep = random.randint(*SLEEP_RANGE)
        # print(f"Sleeping for {time_sleep} seconds...")
        logging.info(f"Sleeping for {time_sleep} seconds...")
        await asyncio.sleep(time_sleep)

        try:
            next_batch = await result.next()
            if not next_batch:
                # print("No more tweets found.")
                logging.info("No more tweets found.")
                break
            collected.extend(next_batch)
            # print(f"New batch: {len(next_batch)} tweets | Total: {len(collected)}")
            logging.info(f"New batch: {len(next_batch)} tweets | Total: {len(collected)}")
            result = next_batch
            attempts = 0
        except (TooManyRequests, HTTPError) as e:
            if e.status_code == 429:
                # print("Rate limit exceeded. Waiting 60 seconds...")
                # logging.info("Rate limit exceeded. Waiting 60 seconds...")  
                reset_time = int(result.headers.get('x-rate-limit-reset', 60))
                logging.info(f"Rate limit exceeded. Waiting until {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(reset_time))}...")
                # Calculate the time to wait until the rate limit resets
                logging.info(f"Rate limit reset time: {int(result.headers.get('x-rate-limit-reset', time.time() + 60))}")
                await asyncio.sleep(reset_time - time.time() + 1)
                attempts += 1
            
            if e.status_code == 404:
                logging.warning(f"404 on {QUERY}, retrying...")
                await asyncio.sleep(5)
                continue
            raise

    return [[tweet.text for tweet in collected[:MAX_TWEETS]] , [tweet.favorite_count for tweet in collected[:MAX_TWEETS]], [tweet.reply_count for tweet in collected[:MAX_TWEETS]], [tweet.retweet_count for tweet in collected[:MAX_TWEETS]]]