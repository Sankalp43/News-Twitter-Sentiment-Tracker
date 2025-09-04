#!/bin/bash
set -e

echo "Running Python initialization script..."
python3 /docker-entrypoint-initdb.d/init_db.py
