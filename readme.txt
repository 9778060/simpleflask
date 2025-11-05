VENV:
Install - python3 -m venv venv
Activate - venv\Scripts\activate
Deactivate - deactivate

REQUIREMENTS INSTALL:
Install - pip install -r requirements.txt

RUN (main app):
$env:FLASK_APP = "main.py"
$env:FLASK_ENV = "development"
flask run

$env:FLASK_ENV = "production"

RUN (DB - Alembic):
$env:FLASK_APP = "main.py"
flask db

flask db init

flask db migrate -m"initial migration"

flask db upgrade
flask db upgrade --sql

flask db history

flask db downgrade ...

RUN (DB):
$env:FLASK_APP = "manage.py"
flask shell

RUN (Celery):
1: App:
$env:FLASK_APP = "main.py"
flask shell

2: Worker:
celery -A celery_runner worker --loglevel=info -P solo

3: Beat
celery -A celery_runner beat --loglevel=info

4: Flower
celery -A celery_runner flower --loglevel=info

RUN (DOCKER):
docker-compose up -d

NEW LANGUAGE (BABEL):
Init - pybabel init -i ./babel/messages.pot -d ./webapp/translations -l pt

Search text - pybabel extract -F ./babel/babel.cfg -o ./babel/messages.pot --input-dirs=.

Update - pybabel update -i ./babel/messages.pot -d ./webapp/translations

Compile - pybabel compile -d ./webapp/translations