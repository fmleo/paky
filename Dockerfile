ARG PYTHON_VERSION=3.12-slim-bullseye

FROM python:${PYTHON_VERSION}

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN mkdir -p /code

WORKDIR /code

COPY . /code

COPY .env.prod /code/.env

RUN pip install -r requirements.txt

RUN python manage.py collectstatic --noinput

RUN python manage.py migrate

RUN python manage.py loaddata grupos setores

EXPOSE ${PORT}