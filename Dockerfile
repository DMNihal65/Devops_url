FROM python:3.9-alpine

WORKDIR /app

COPY app.py .

CMD ["python", "app.py"]