FROM python:3.10-slim-bookworm

ARG PIP_VERSION=26.2

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir "pip==${PIP_VERSION}" \
  && useradd --create-home --shell /usr/sbin/nologin appuser

WORKDIR /app
COPY ./requirements.txt /app
RUN pip install --no-cache-dir --requirement /app/requirements.txt
COPY --chown=appuser:appuser . /app

USER appuser

EXPOSE 8080

CMD ["gunicorn", "--bind=0.0.0.0:8080", "--workers=2", "--timeout=60", "server:server"]
