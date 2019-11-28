#!/bin/bash


echo -e "\e[1;96mDelete current database"
rm -f db.sqlite3
rm -f annotate/migrations/00*.py

python manage.py makemigrations
python manage.py migrate
python manage.py populate_toy
