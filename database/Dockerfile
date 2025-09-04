FROM postgres:16-bullseye

# # Install Python and pip easily on Debian-based image
RUN apt-get update && apt-get install -y python3 python3-pip python3-dev libpq-dev gcc

# # Install psycopg2-binary via pip separately
RUN pip install psycopg2-binary


# Copy initialization scripts into the container (if needed)
COPY scripts/init-db.sh /docker-entrypoint-initdb.d/
COPY scripts/init_db.py /docker-entrypoint-initdb.d/

# Ensure initialization scripts are executable (if applicable)
RUN chmod +x /docker-entrypoint-initdb.d/init-db.sh \
             /docker-entrypoint-initdb.d/init_db.py


EXPOSE 5432


