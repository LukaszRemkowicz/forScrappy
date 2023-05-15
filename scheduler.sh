#!/bin/bash

cd /path/to/app
source .env

pipenv shell

python python cli.py get-forum-links -link "${LOCAL__BASE_URL}trance/" -p 5


# 1. chmod +x scheduler.sh
# 2. cron: sudo crontab -e
# 3. 0 1 * * * /path/to/scheduler.sh
