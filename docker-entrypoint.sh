#!/bin/sh

echo "Make database migrations"
alembic upgrade head

echo "Starting server"
gunicorn -w 3 runserver:init_app -b unix:/app/socket/wsgi.socket --worker-class aiohttp.GunicornWebWorker