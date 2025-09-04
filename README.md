
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

