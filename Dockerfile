FROM python:3.11
WORKDIR /app

COPY requirements.txt ./
RUN pip install -r requirements.txt

CMD ["gunicorn", "-c", "config.py", "app:app"]