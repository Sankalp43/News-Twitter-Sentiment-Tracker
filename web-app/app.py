# app.py
import os
import psycopg2
import logging
from flask import Flask, render_template, request, jsonify
from datetime import datetime
import base64
from dotenv import load_dotenv
import csv
from tweet_relevance.infer import predict_relevance  # Import the predict_relevance function

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv(override=True)
app = Flask(__name__)

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            dbname=os.getenv('POSTGRES_DB'),
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD'),
            port="5432"
        )
        return conn
    except Exception as e:
        logging.error(f"Database connection failed: {e}")
        raise

@app.route('/')
def index():
    filter_date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    logging.info(f"Fetching articles for date: {filter_date}")

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT 
                a.id, a.title, a.image, a.summary, a.weblink, a.publication_timestamp,
                a.TweetSummary, a.NewsSummary,
                t.id as tweet_id, t.tweet_text, t.tweet_likes, t.tweet_retweets, t.tweet_replies
            FROM articles a
            LEFT JOIN tweets t ON a.id = t.article_id
            WHERE DATE(a.publication_timestamp) = %s
            ORDER BY a.publication_timestamp DESC;
        """, (filter_date,))
        
        rows = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        logging.error(f"Failed to fetch data from database: {e}")
        return render_template('index.html', articles=[], filter_date=filter_date)

    articles_dict = {}
    for row in rows:
        try:
            article_id, title, image, summary, weblink, pub_time, tweet_summary, news_summary, tweet_id, tweet_text, tweet_likes, tweet_retweets, tweet_replies = row
            
            if article_id not in articles_dict:
                if image:
                    base64_image = base64.b64encode(image).decode('utf-8')
                    image_src = f"data:image/jpeg;base64,{base64_image}"
                else:
                    image_src = None
                
                articles_dict[article_id] = {
                    "id": article_id,
                    "title": title,
                    "image_src": image_src,
                    "summary": summary,
                    "weblink": weblink,
                    "publication_timestamp": pub_time,
                    "tweet_summary": tweet_summary,
                    "news_summary": news_summary,
                    "tweets": []
                }
            
            if tweet_id:
                relevance_result = predict_relevance(title, tweet_text)
                articles_dict[article_id]["tweets"].append({
                    "tweet_id": tweet_id,
                    "tweet_text": tweet_text,
                    "tweet_likes": tweet_likes,
                    "tweet_retweets": tweet_retweets,
                    "tweet_replies": tweet_replies,
                    "relevant": relevance_result["relevant"],
                    "confidence": relevance_result["confidence"]
                })
        except Exception as e:
            logging.warning(f"Error processing article or tweet row: {e}")
            continue

    # Sort tweets by confidence and limit to top 10 for each article
    for article in articles_dict.values():
        article["tweets"] = sorted(
            article["tweets"], 
            key=lambda x: x["confidence"], 
            reverse=True
        )[:10]

    articles = list(articles_dict.values())

    return render_template('index.html', articles=articles, filter_date=filter_date)

FEEDBACK_FILE = "./tweet_relevance/feedback_log.csv"

@app.route('/feedback', methods=['POST'])
def log_feedback():
    try:
        data = request.json
        headline = data.get('headline')
        tweet = data.get('tweet')
        user_label = data.get('user_label')

        if headline is None or tweet is None or user_label is None:
            logging.warning("Invalid feedback data received")
            return jsonify({'message': 'Invalid feedback data'}), 400

        new_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "headline": headline,
            "tweet": tweet,
            "user_label": int(user_label)
        }

        file_exists = os.path.exists(FEEDBACK_FILE)
        with open(FEEDBACK_FILE, mode="a", newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=new_entry.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(new_entry)

        logging.info(f"Feedback recorded: {new_entry}")
        return jsonify({'message': 'Feedback recorded successfully'})

    except Exception as e:
        logging.error(f"Failed to log feedback: {e}")
        return jsonify({'message': 'Internal server error'}), 500

if __name__ == '__main__':
    logging.info("Starting Flask server...")
    app.run(host='0.0.0.0', port=5000)
