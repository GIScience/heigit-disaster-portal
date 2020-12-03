#! /usr/bin/env bash

echo "INFO: Pre-start script starting"

# Let the DB start
python ./app/db/pre_start.py

# Run migrations
alembic upgrade head

# Create initial data in DB
python ./app/db/init_db.py

echo "INFO: Pre-start script finished"
