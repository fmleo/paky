ARG PYTHON_VERSION=3.12-slim-bullseye

FROM python:${PYTHON_VERSION}
COPY --from=ghcr.io/astral-sh/uv:0.12.24 /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/code/.venv/bin:$PATH"

RUN mkdir -p /code

WORKDIR /code

COPY pyproject.toml uv.lock /code/

RUN uv sync --locked --no-dev --no-install-project

COPY . /code

COPY .env.prod /code/.env

RUN python manage.py collectstatic --noinput

RUN python manage.py migrate

RUN python manage.py loaddata grupos setores

EXPOSE ${PORT}
