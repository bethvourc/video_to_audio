FROM python:3.10-slim-bookworm

ARG PIP_VERSION=26.2

ENV PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1

RUN apt-get update \
  && apt-get install -y --no-install-recommends --no-install-suggests \
  ffmpeg \
  && pip install --no-cache-dir "pip==${PIP_VERSION}" \
  && useradd --create-home --shell /usr/sbin/nologin appuser \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY ./requirements.txt /app
RUN pip install --no-cache-dir --requirement /app/requirements.txt
COPY --chown=appuser:appuser . /app

USER appuser

CMD ["python3", "consumer.py"]
