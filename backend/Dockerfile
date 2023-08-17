FROM python:3.8
WORKDIR /app
RUN pip install gunicorn==20.1.0
COPY requirements.txt .
RUN apt-get update && apt-get upgrade -y && \
    pip install --upgrade pip && pip install -r requirements.txt --no-cache-dir --default-timeout=100
COPY . .
WORKDIR ./foodgram
CMD ["gunicorn", "foodgram.wsgi", "--bind", "0:8080" ]