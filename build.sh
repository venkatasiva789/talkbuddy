#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

python -c "
from app import app, db
from seed_data import seed

with app.app_context():
    db.create_all()

seed()
"
