#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python club_management/manage.py collectstatic --no-input
python club_management/manage.py migrate