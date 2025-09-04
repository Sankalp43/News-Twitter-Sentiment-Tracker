import os
import feedparser
import psycopg2
import requests
import time
from datetime import datetime
from dotenv import load_dotenv
from psycopg2.extras import execute_values
import logging
load_dotenv(override=True)
from psycopg2.extras import execute_batch
import asyncio
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry_if_exception_type
import concurrent.futures

RSS_FEED_URL = os.getenv('RSS_FEED_URL')
# print(RSS_FEED_URL)
POLL_INTERVAL = int(os.getenv('POLL_INTERVAL', 600))

# Database credentials from environment variables
DB_HOST = os.getenv('DB_HOST')
DB_NAME = os.getenv('POSTGRES_DB')
DB_USER = os.getenv('POSTGRES_USER')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD')

# Feed dictionary paths (for flexibility)
FEED_TITLE_PATH = os.getenv('FEED_TITLE_PATH', 'title')
FEED_PUBLISHED_PATH = os.getenv('FEED_PUBLISHED_PATH', 'published')
FEED_TAGS_PATH = os.getenv('FEED_TAGS_PATH', 'tags')
FEED_SUMMARY_PATH = os.getenv('FEED_SUMMARY_PATH', 'summary')
FEED_LINK_FIELD = os.getenv('FEED_LINK_FIELD', 'link')
FEED_IMAGE_FIELD= os.getenv('FEED_IMAGE_FIELD', 'media_content')

import requests
import logging

API_URL_TWEETS = "http://127.0.0.1:8000/twitter/tweets"
API_URL_NEWS = "http://127.0.0.1:8000/news/summarize"


print("Starting RSS Feed Reader...", flush=True)

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,  # Set logging level
        format='%(asctime)s - %(levelname)s - %(message)s',  # Log format
        handlers=[
            logging.StreamHandler()  # Send logs to stdout
        ]
    )

@retry(
    wait=wait_exponential(multiplier=1, min=4, max=60),
    stop=stop_after_attempt(5),
)
def get_summary(url: str, timeout: int = 120):
    try:
        response = requests.post(
            API_URL_NEWS,
            json={"url": url},
            timeout=timeout
        )
        return response.json()
    except requests.exceptions.Timeout:
        logging.warning(f"Timeout summarizing {url}")
        return {"error": "Timeout occurred"}
    except Exception as e:
        logging.error(f"Error for {url}: {str(e)}")
        return {"error": str(e)}

import psycopg2
import logging

def get_weblinks_without_news_summary():
    """Fetch all weblinks from articles where NewsSummary is NULL, empty, or only whitespace."""
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port="5432"
        )
        cur = conn.cursor()
        cur.execute("""
            SELECT weblink FROM articles
            WHERE NewsSummary IS NULL OR TRIM(NewsSummary) = ''
        """)
        weblinks = [row[0] for row in cur.fetchall()]
    except Exception as e:
        logging.error(f"Database error: {e}")
        weblinks = []
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()
    return weblinks

def update_news_summaries():
    """For each article without a NewsSummary, generate and store the summary."""
    weblinks = get_weblinks_without_news_summary()
    if not weblinks:
        logging.info("No articles require NewsSummary updates.")
        return
    updated_count = 0
    logging.info(f"Found {len(weblinks)} articles without NewsSummary.")
    for weblink in weblinks:
        if not weblink.startswith("http"):
            logging.error(f"Invalid URL: {weblink}")
            continue

        try:
            result = get_summary(weblink)
            if "summary" in result:
                summary=result["summary"]
            else:
                summary= (result.get("error", "Summary failed"))
            if summary and summary != "No article text could be extracted." and summary != "Summary failed":
                logging.info(f"Summary generated for {weblink}: {summary}")
                # Update the NewsSummary in the database
                try:
                    conn = psycopg2.connect(
                        dbname=DB_NAME,
                        user=DB_USER,
                        password=DB_PASSWORD,
                        host=DB_HOST,
                        port="5432"
                    )
                    cur = conn.cursor()
                    cur.execute("""
                        UPDATE articles SET NewsSummary = %s
                        WHERE weblink = %s
                    """, (summary, weblink))
                    updated_count += cur.rowcount
                    logging.info(f"Updated NewsSummary for {weblink}")
                    conn.commit()
                except Exception as e:
                    logging.error(f"Failed to update NewsSummary for {weblink}: {e}")
                finally:
                    if 'cur' in locals(): cur.close()
                    if 'conn' in locals(): conn.close()
            else:
                logging.warning(f"Summary could not be generated for {weblink}")
        except Exception as e:
            logging.error(f"Error summarizing {weblink}: {e}")

    logging.info(f"Updated {updated_count} NewsSummaries in the database.")

def insert_articles(titles, timestamps, weblinks, images, tags_list, summaries , TweetSummaries=None, NewsSummaries=None):
    try:
        # print(f"Connecting to database at {DB_HOST}...", flush=True)
        logging.info(f"Connecting to database at {DB_HOST}...")
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port="5432"
            

        )
        # print("Database connection successful!", flush=True)
        logging.info("Database connection successful!")
        cur = conn.cursor()

        # Define the SQL query template
        insert_query = """
        INSERT INTO articles (title, publication_timestamp, weblink, image, tags, summary, TweetSummary, NewsSummary) 
        VALUES %s
        ON CONFLICT (title, weblink) DO NOTHING;          
        """


        # Prepare data for batch insertion
        records = [
            (titles[i], timestamps[i], weblinks[i], psycopg2.Binary(images[i]) if images[i] else None, tags_list[i], summaries[i], TweetSummaries[i] if TweetSummaries else None, NewsSummaries[i] if NewsSummaries else None)
            for i in range(len(titles))
        ]

        # Execute batch insert
        execute_values(cur, insert_query, records)

        # Commit changes
        conn.commit()

        inserted_count = cur.rowcount

        cur.close()
        conn.close()

        # print(f"{inserted_count} articles inserted successfully!")
        logging.info(f"{inserted_count} new articles inserted successfully!")
    except Exception as e:
        logging.error("Error:", e)
        print("Error:", e)

def fetch_and_store_feed():
    feed = feedparser.parse(RSS_FEED_URL)
    if feed.bozo:
        logging.error(f"Failed to parse RSS feed: {feed.bozo_exception}")
        # print("Failed to parse RSS feed:", feed.bozo_exception)
        return
    
    titles = []
    publication_date = []
    weblinks = []
    summaries = []
    images_url = []
    tags = []
    images = []
    for entry in feed.entries:
        # print(entry)
        titles.append(entry.get(FEED_TITLE_PATH, '').strip())
        publication_date.append(entry.get(FEED_PUBLISHED_PATH, ''))
        weblinks.append(entry.get(FEED_LINK_FIELD, ''))
        summaries.append(entry.get(FEED_SUMMARY_PATH, ''))
        # print(FEED_IMAGE_FIELD)
        media = entry.get(FEED_IMAGE_FIELD, None)
        # print(media)
        # print("#"*50)
        image_url = None
        if media:
            image_url = media[0]['url']
        images_url.append(image_url)
        tag = entry.get(FEED_TAGS_PATH, '')
        tag_to_append = []
        if isinstance(tag, list):
            no_none = []
            for t in tag:
                (no_none.extend(list(t.values())))
            for t in no_none:
                if t:
                        tag_to_append.append(t)    
        tags.append(tag_to_append)

   
        if image_url:
            # print(f"Downloading image: {image_url}")
            try:
                img_resp = requests.get(image_url, timeout=10)
                if img_resp.status_code == 200:
                    image_data = img_resp.content
                    # print(image_data)
                else:
                    image_data = None
            except Exception as e:
                print(f"Image download failed: {e}")
                image_data = None
        else:
            image_data = None

        images.append(image_data)

    logging.info(f"Fetched {len(titles)} articles from the feed.")
    logging.info("Getting summaries for the articles...")

    logging.info(f"Inserting {len(titles)} articles into the database...")
    insert_articles(titles= titles, timestamps=publication_date, weblinks = weblinks, images = images, tags_list=tags, summaries=summaries , TweetSummaries=None, NewsSummaries=None)
    logging.info("Articles inserted successfully!")

        
def fetch_processed_tweets(title):
    try:
        logging.info(f"Fetching tweets for '{title}'...")
        response = requests.post(
            API_URL_TWEETS,
            json={"title": title, "max_tweets": 20},
            timeout=120
        )
        if response.status_code == 404:
            logging.warning(f"No tweets found for '{title}' (404)")
            return None
        elif response.status_code != 200:
            logging.error(f"Error fetching tweets for '{title}': {response.status_code} {response.text}")
            return None
        return response.json()
    except requests.exceptions.Timeout:
        logging.warning(f"Timeout fetching tweets for '{title}'")
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Request error for '{title}': {e}")
        return None

def get_titles_without_tweet_summary():
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port="5432"
    )
    cur = conn.cursor()
    cur.execute("""
        SELECT title FROM articles
        WHERE TweetSummary IS NULL OR TRIM(TweetSummary) = ''
    """)
    titles = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return titles
        
def get_tweets_and_summaries():
    # Get titles from the database
    titles = get_titles_without_tweet_summary()
    if not titles:
        logging.info("No titles found without tweet summaries.")
        return
    
    logging.info(f"Found {len(titles)} titles without tweet summaries.")

    # titles  = titles[:5]  # Limit to first 5 titles for testing
    tweets = []
    tweets_likes = []
    tweets_replies = []
    tweets_retweets = []
    tweets_summary = []
    logging.info("Getting tweets for the articles...")    
    

    # Usage in your loop
    for title in titles:
        result = fetch_processed_tweets(title)
        if result:
            tweets.append(result["cleaned_tweets"])
            tweets_summary.append(result["summary"])
            tweets_likes.append(result["raw_stats"]["likes"])
            tweets_replies.append(result["raw_stats"]["replies"])
            tweets_retweets.append(result["raw_stats"]["retweets"])
        else:
            logging.error(f"Failed to fetch tweets for '{title}'")
            tweets.append([])
            tweets_likes.append(0)
            tweets_replies.append(0)
            tweets_retweets.append(0)
            tweets_summary.append("No summary available")
        # Process raw stats as needed

    logging.info(f"Fetched tweets for {len(tweets)} articles.")
    logging.info("Inserting tweets into the database...")

    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port="5432"
        )
        cur = conn.cursor()

        # Get article ids from the database
        cur.execute("SELECT id, title FROM articles")
        article_ids = cur.fetchall()

        # Create a dictionary mapping article titles to IDs
        article_ids_dict = {title: id for id, title in article_ids}

        # Prepare data for batch insertion
        batch_insert_data = []

        # Loop over each title and prepare tweet data for batch insertion
        for i, title in enumerate(titles):
            # Ensure the title exists in article_ids_dict
            article_id = article_ids_dict.get(title)
            
            if article_id:
                logging.info(f"Preparing tweet data for article '{title}' (ID: {article_id})...")

                # Loop through each tweet for this article and prepare data for insertion
                for j in range(len(tweets[i])):  # Loop over all tweets for the article
                    tweet = tweets[i][j]
                    tweet_likes = tweets_likes[i][j]
                    tweet_replies = tweets_replies[i][j]
                    tweet_retweets = tweets_retweets[i][j]

                    # Add this tweet data as a tuple to the batch insert data list
                    batch_insert_data.append((article_id, tweet, tweet_likes, tweet_replies, tweet_retweets))

                logging.info(f"Prepared {len(tweets[i])} tweets for insertion for article '{title}' (ID: {article_id})")

            else:
                logging.error(f"Article ID for title '{title}' not found.")

        # Now insert the prepared data using execute_batch (batch insertion)
        if batch_insert_data:
            logging.info("Inserting tweet data in batch...")
            insert_query = """
                INSERT INTO tweets (article_id, tweet_text, tweet_likes, tweet_replies, tweet_retweets)
                VALUES (%s, %s, %s, %s, %s)
            """
            try:
                execute_batch(cur, insert_query, batch_insert_data, page_size=100)  # page_size can be adjusted for optimal batch size
                logging.info(f"Batch insert completed: {len(batch_insert_data)} rows inserted.")
                
                # Commit the transaction
                conn.commit()

            except Exception as e:
                logging.error(f"Error inserting tweet data in batch: {e}")
                conn.rollback()  # Rollback in case of error

        # Close the cursor and connection
        cur.close()
        conn.close()
        logging.info("All tweet data has been inserted successfully.")

    except Exception as e:
        logging.error(f"Error connecting to the database: {e}")
        print(f"Error connecting to the database: {e}")
    # adding the tweets summaries to the database
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port="5432"
        )
        cur = conn.cursor()
        update_query = """
        UPDATE articles SET TweetSummary = %s WHERE title = %s;
        """
        
        records = [
            (tweets_summary[i], titles[i])
            for i in range(len(tweets_summary))
        ]
    
        # Execute batch insert
        cur.executemany(update_query, records)

        # Commit changes
        conn.commit()

        inserted_count = cur.rowcount

        cur.close()
        conn.close()

        logging.info(f"{inserted_count} tweets summaries inserted successfully!")
    except Exception as e:
        logging.error("Error:", e)
        print("Error:", e)
            

if __name__ == "__main__":
    import time
    setup_logging()
    logging.getLogger("twikit").setLevel(logging.WARNING)

    POLL_INTERVAL=int(os.getenv("POLL_INTERVAL", 30))
    POLL_INTERVAL = 300
    # RSS_FEED_URL=os.getenv("RSS_FEED_URL")
    rss_feed_urls = os.getenv("RSS_FEED_URLS", "").split(',')
    # print(rss_feed_urls)
    
    while True:
        for RSS_FEED_URL in rss_feed_urls:
            print(f"Fetching RSS feed from {RSS_FEED_URL}...")
            try:
                logging.info(f"Fetching RSS feed from {RSS_FEED_URL}...")
                # print(f"Fetching RSS feed from {RSS_FEED_URL}...")

                fetch_and_store_feed()
                with concurrent.futures.ThreadPoolExecutor() as executor:
                # Submit both functions to the thread pool
                    future1 = executor.submit(update_news_summaries)
                    future2 = executor.submit(get_tweets_and_summaries)
                    
                    # Wait for both to finish (optional, for logging/completion)
                    concurrent.futures.wait([future1, future2])
                    logging.info("Both update_news_summaries and get_tweets_and_summaries are done.")
            except Exception as e:
                logging.error(f'Error fetching and storing feed: {e}')
            break
        logging.info(f"Sleeping for {POLL_INTERVAL} seconds...")
        time.sleep(POLL_INTERVAL)




