# News Twitter Sentiment Project

## 📌 Overview

The **Twitter News Sentiment Project** is an AI-driven system that aggregates news from RSS feeds, collects related tweets, applies **Natural Language Processing (NLP)** for summarization and sentiment analysis, and serves the results through a web interface.

The project is designed with two main parts:

1. **Backend Pipeline** – Fetching, cleaning, deduplicating, summarizing, and storing news + tweets.
2. **Web Interface** – Allowing users to explore articles, view relevant tweets, and provide feedback that improves the system through continuous learning.

---

## 🔄 System Architecture

### High-Level Flow&#x20;

1. **News Ingestion**

   * Poll RSS feeds every 10 minutes using **Feedparser**
   * Extract metadata (title, link, date, image, etc.)
   * Store in **PostgreSQL (articles table)**

2. **Tweet Collection & Cleaning**

   * Fetch tweets using **Twikit**
   * Clean with regex (remove URLs, hashtags, mentions)

3. **Deduplication**

   * Use **Sentence-BERT embeddings** + **DBSCAN** to cluster similar tweets
   * Select representative tweets

4. **Summarization**

   * Combine headlines + deduplicated tweets
   * Summarize using fine-tuned **T5-base model**

5. **Database Storage**

   * Store articles & tweets in PostgreSQL
   * Bulk insertions with async operations

6. **Feedback-Driven Web Interface**

   * Flask-based app shows news + tweet summaries
   * Users vote on tweet relevance ("Relevant" / "Not Relevant")
   * Feedback logged for **continuous retraining**

---

## ⚙️ Low-Level Design&#x20;

* **Modules**

  1. **RSS Reader** → Extracts news + metadata, checks duplicates, stores in DB.
  2. **Twitter Module** → Fetches, cleans, deduplicates tweets, generates sentiment summary.
  3. **News Summary** → Extracts full article text, summarizes via **T5-base**.

* **APIs**

  * `http://127.0.0.1:8000/twitter/tweets`
  * `http://127.0.0.1:8000/news/summarize`

* **Database**

  * **PostgreSQL** with `articles` and `tweets` tables

* **Models & Tools**

  * Summarization: **Hugging Face T5-base**
  * Classification: **Scikit-learn** model (feedback-based)
  * Pipeline Tracking: **DVC**
  * Monitoring: **Prometheus (9090)**, **Grafana (3000)**
  * Deployment: **Docker**

---

## 🖥️ User Guide&#x20;

1. **Access News by Date**

   * Use the "Filter by Date" field to select articles by `DD/MM/YYYY`.

2. **View Headlines & Summaries**

   * Each article shows:

     * Headline (clickable link)
     * **Tweet Summary**
     * **News Summary**

3. **Read Full Articles**

   * Click headline to open full article.

4. **View Related Tweets**

   * Click "Show/Hide Top Tweets"
   * See tweets + engagement stats (likes, retweets, replies) + **confidence score**

5. **Provide Feedback**

   * Mark tweets as **Relevant** (✅) or **Not Relevant** (❌)
   * Feedback improves system via retraining

---

## 📊 Monitoring & Deployment

* **Dockerized** setup with containers for:

  * Web App (Flask)
  * Database (PostgreSQL)
  * Monitoring (Prometheus + Grafana)
  * Node Exporter

* **Default Ports**

  * Flask: `5000`
  * PostgreSQL: `5432`
  * Prometheus: `9090`
  * Grafana: `3000`
  * Node Exporter: `9100`

---

## 🚀 Getting Started

### Prerequisites

* Python 3.9+
* PostgreSQL
* Docker & Docker Compose

### Setup

```bash
# Clone repo
git clone https://github.com/yourusername/twitter-news-sentiment.git
cd twitter-news-sentiment

# Setup virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations (if any)
# Launch APIs
uvicorn main:app --reload

# Run Flask web app
python app.py
```

### Using Docker

```bash
docker-compose up --build
```

---

## 🛠 Tech Stack

* **Backend**: FastAPI, Flask
* **NLP Models**: Hugging Face T5, Sentence-BERT
* **Database**: PostgreSQL
* **Pipeline & CI/CD**: DVC, Docker
* **Monitoring**: Prometheus, Grafana
* **Frontend**: Flask-based UI

---

## 📈 Future Improvements

* Expand sentiment analysis with more fine-grained emotions
* Add multi-language support
* Improve summarization with LLMs (e.g., GPT-family)
* Advanced visualization dashboard for trends

---


# Docker Compose Project Report

## Project Overview
This project consists of three Docker containers managed by a `docker-compose.yaml` file. The containers represent the following services:

1. **Database (PostgreSQL)**
2. **RSS Reader Application**
3. **Web Application**

The folder structure is organized into subdirectories for each service with corresponding Dockerfiles and scripts.

## Folder Structure
```
├── database/
│   ├── scripts/
│   │    ├── init_db.py
│   │    └── init-db.sh
│   └── Dockerfile
├── rss-reader/
│   ├── scripts/
│   │    ├── requirements.txt
│   │    ├── rss_feed_reader.py
│   │    └── run_rss_reader.sh
│   └── Dockerfile
├── web-app/
│   ├── templates/
│   │    └── index.html
│   ├── app.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── run_web_app.sh
├── .env      # MAKE SURE YOU CREATE THIS .env FILE BEFORE BUILDING AND RUNNING THE CONTAINER, DETAILS GIVEN ABOVE.
├── docker-compose.yaml
└── readme.md
```

## Service Descriptions

### 1. Database Service
- **Container Name:** `postgres_article_db`
- **Build Context:** `./database`
- **Ports:** 5432:5432
- **Environment Variables:**
  - `POSTGRES_USER`
  - `POSTGRES_PASSWORD`
  - `POSTGRES_DB`
- **Volume:** `article_db_volume` (to persist data)
- **Health Check:** Checks database readiness using `pg_isready` command.

### 2. RSS Reader Service
- **Container Name:** `rss_feed_reader_app`
- **Build Context:** `./rss-reader`
- **Depends On:** `db` (Waits for the database to be healthy)
- **Environment Variables:**
  - `RSS_FEED_URL`
  - `POLL_INTERVAL`
  - `DB_HOST`
  - `POSTGRES_USER`
  - `POSTGRES_PASSWORD`
  - `POSTGRES_DB`

### 3. Web Application Service
- **Container Name:** `web_app_container`
- **Build Context:** `./web-app`
- **Ports:** 5000:5000
- **Depends On:** `db` (Waits for the database to be healthy)
- **Environment Variables:**
  - `DB_HOST`
  - `POSTGRES_USER`
  - `POSTGRES_PASSWORD`
  - `POSTGRES_DB`

## Docker Commands

### Build Containers
```bash
docker-compose build
```

### Run Containers
```bash
docker-compose up -d
```

### Start Containers
```bash
docker-compose start
```

### Stop Containers
```bash
docker-compose stop
```

### Remove Containers
```bash
docker-compose down
```

### View Logs

#### Database Logs
```bash
docker logs postgres_article_db
```

#### RSS Reader Logs
```bash
docker logs rss_feed_reader_app
```

#### Web Application Logs
```bash
docker logs web_app_container
```

### Check Container Status
```bash
docker-compose ps
```

### Execute a Shell in a Running Container

#### Database
```bash
docker exec -it postgres_article_db bash
```

#### RSS Reader
```bash
docker exec -it rss_feed_reader_app bash
```

#### Web Application
```bash
docker exec -it web_app_container bash
```


## Additional Considerations
1. **Data Persistence:**
   - PostgreSQL data is stored in the `article_db_volume` Docker volume.
2. **Service Dependencies:**
   - RSS Reader and Web App depend on the PostgreSQL service being ready before starting.
3. **Health Check:**
   - Ensures that the database is fully ready before the other services attempt to connect.

## Troubleshooting
1. Check if containers are running:
```bash
docker ps
```

2. Restart specific containers:
```bash
docker-compose restart <service_name>
```

3. Inspect network connectivity:
```bash
docker network ls
docker network inspect <network_name>
```


## Create a .env file to create the containers. Make sure it contains these configurations.
## Environment Configuration
The `.env` file stores sensitive environment variables. Ensure it contains:

```
# Database configuration variables
POSTGRES_USER=postgres # yOUR POSTGRES USER
POSTGRES_PASSWORD=8881 # YOUR POSTGRES PASSWORD
POSTGRES_DB=postgres   # YOUR POSTGRES DB

# RSS Feed configuration (The Hindu as example)
RSS_FEED_URL=https://www.thehindu.com/news/national/?service=rss

# Polling interval in seconds (default 10 mins)
POLL_INTERVAL=600

# Database connection details for RSS Reader app
DB_HOST=db  # Use Docker service name to connect within the network

# Feed dictionary paths (optional customization for different feeds)
FEED_TITLE_PATH=title  
FEED_PUBLISHED_PATH=published  
FEED_LINK_FIELD=link  
FEED_IMAGE_FIELD=media_content
FEED_SUMMARY_PATH=summary  
FEED_TAGS_PATH=tags
```
uvicorn main:main_app --workers 4 --timeout-keep-alive 120
python rss-reader/scripts/rss_feed_reader.py
python app.py
