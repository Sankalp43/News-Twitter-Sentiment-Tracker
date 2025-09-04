#!/usr/bin/env python3
import logging
import os
import psycopg2
import sys
from dotenv import load_dotenv
load_dotenv(override=True)
def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
    ) 

def initialize_db():
    dbname = os.getenv('POSTGRES_DB')
    user = os.getenv('POSTGRES_USER')
    password = os.getenv('POSTGRES_PASSWORD')

    print(f"Connecting to database {dbname} as user {user}...")
    print(f'password: {password}')
    # Connect via Unix socket explicitly
    try:
        logging.info("Initializing database and tables.")
        conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host='localhost',  # <-- FIXED HERE
            port='5432',  # <-- FIXED HERE
            # host='/var/run/postgresql'  # <-- FIXED HERE  # Uncomment if using Unix socket
            

        )
        logging.info("Connected to the database.")
        cursor = conn.cursor()
        logging.info("Creating table.")
        create_table_query = '''
        CREATE TABLE IF NOT EXISTS articles (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL CHECK (title <> ''),
            publication_timestamp TIMESTAMP NOT NULL,
            weblink TEXT NOT NULL CHECK (weblink <> ''),
            image BYTEA,
            tags TEXT[],
            summary TEXT,
            UNIQUE (title, weblink),
            TweetSummary TEXT,
            NewsSummary TEXT
        );
        '''



        cursor.execute(create_table_query)
        conn.commit()
        cursor.close()


        logging.info("Creating Tweet table.")
        create_tweet_table_query = '''
        CREATE TABLE IF NOT EXISTS tweets (
            id SERIAL PRIMARY KEY,
            article_id INTEGER REFERENCES articles(id) ON DELETE CASCADE,
            tweet_text TEXT NOT NULL CHECK (tweet_text <> ''),
            tweet_likes INTEGER,
            tweet_retweets INTEGER,
            tweet_replies INTEGER
                    );

        '''
        cursor = conn.cursor()
        cursor.execute(create_tweet_table_query)
        conn.commit()
        cursor.close()


        logging.info("Created Tweet table.")


        conn.close()
        logging.info("Database and tables initialized successfully.")
        # print("Database and tables initialized successfully.")



    except Exception as e:
        # print(f"Initialization error: {e}")
        logging.error(f"Initialization error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    dbname = os.getenv('POSTGRES_DB')
    user = os.getenv('POSTGRES_USER')
    password = os.getenv('POSTGRES_PASSWORD')

    print(f"Connecting to database {dbname} as user {user}...")
    print(f'password: {password}')
    setup_logging()
    initialize_db()
