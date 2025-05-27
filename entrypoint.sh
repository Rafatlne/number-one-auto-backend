#!/bin/bash
set -e

echo "Waiting for database..."
./wait-for-it.sh db:5432 --timeout=30 --strict

until cd /app/
do
    echo "Waiting for server volume ..."
done

until python manage.py migrate
do
    echo "Waiting for db to be ready ..."
    sleep 2
done

echo "Populating countries..."
python manage.py populate_countries

echo "Populating sources..."
python manage.py populate_sources

echo "Starting background tasks..."
python manage.py start_background_tasks

echo "Starting Swagger documentation..."
python manage.py spectacular --color --file schema.yml

echo "Starting Django server..."
python manage.py runserver 0.0.0.0:8000
