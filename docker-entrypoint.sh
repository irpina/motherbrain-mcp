#!/bin/bash
set -e

# Create tables first using SQLAlchemy
echo "Creating database tables..."
python -c "
import asyncio
import sys
import traceback
sys.path.insert(0, '/app')
try:
    from app.db.init_db import init_db
    asyncio.run(init_db())
    print('Tables created successfully')
except Exception as e:
    print(f'Error creating tables: {e}')
    traceback.print_exc()
    sys.exit(1)
"

# Stamp the database with the current migration version
# This marks all migrations as 'already applied' since SQLAlchemy created the tables
echo "Stamping migration version..."
alembic stamp head

# Start the application
echo "Starting application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
