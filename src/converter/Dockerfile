FROM python:3.10-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1

RUN apt-get update \
  && apt-get install -y --no-install-recommends --no-install-suggests \
  build-essential \
  pkg-config \
  ffmpeg \
  default-libmysqlclient-dev \
  python3-dev \
  && pip install --no-cache-dir --upgrade pip \
  && useradd --create-home --shell /usr/sbin/nologin appuser

WORKDIR /app
COPY ./requirements.txt /app
RUN pip install --no-cache-dir --requirement /app/requirements.txt
COPY . /app
RUN chown -R appuser:appuser /app

USER appuser

CMD ["python3", "consumer.py"]
