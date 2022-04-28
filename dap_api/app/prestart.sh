#! /usr/bin/env bash
python -c 'from app.logger import logger; logger.info("Pre-start script starting")'

# Let the DB start
python ./app/db/pre_start.py

# Run migrations
alembic upgrade head

# Create initial data in DB
python ./app/db/init_db.py

python -c 'from app.logger import logger; logger.info("Pre-start script finished")'
