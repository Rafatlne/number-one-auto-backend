# -----------------------------------------------------
FROM python:3.10
WORKDIR /app

ENV PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir gunicorn
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN DJANGO_SETTINGS_MODULE=conf.settings.dev python manage.py collectstatic --noinput

ENV DJANGO_SETTINGS_MODULE=conf.settings.dev
