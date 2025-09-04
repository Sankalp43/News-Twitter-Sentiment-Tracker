FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY scripts/requirements.txt .
RUN pip install -r requirements.txt

# Copy application files
COPY scripts/rss_feed_reader.py .
COPY scripts/run_rss_reader.sh .

# Make the bash script executable
RUN chmod +x /app/run_rss_reader.sh

ENV PYTHONUNBUFFERED=1

# Set the bash script as the default command
CMD ["/app/run_rss_reader.sh"]






