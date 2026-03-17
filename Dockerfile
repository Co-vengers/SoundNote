FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip wheel "setuptools<81" \
    && pip install --no-cache-dir --no-build-isolation -r /app/requirements.txt

COPY . /app

WORKDIR /app/video_transcriber

EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate && gunicorn video_transcriber.wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 300"]
