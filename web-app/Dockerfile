FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application files
COPY app.py .
COPY templates/ ./templates/
COPY tweet_relevance/ ./tweet_relevance/


# Set the shell script as the default command
CMD ["python", "app.py"]



