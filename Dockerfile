ARG PYTHON_VERSION=3.12-slim-bullseye

FROM python:${PYTHON_VERSION}

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN mkdir -p /code

WORKDIR /code

COPY . /code

RUN pip install -r requirements.txt

RUN python manage.py collectstatic --noinput

RUN python manage.py migrate

ENV DJANGO_SUPERUSER_USERNAME=admin
ENV DJANGO_SUPERUSER_EMAIL=lfm@duck.com
ENV DJANGO_SUPERUSER_PASSWORD=admin


RUN python manage.py loaddata grupos setores

RUN python manage.py createsuperuser --noinput

EXPOSE 8000

CMD ["gunicorn", "--bind", ":8000", "--workers", "2", "paky.wsgi"]
