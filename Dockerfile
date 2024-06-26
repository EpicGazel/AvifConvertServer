FROM python:3.10

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 8080

CMD ["python", "-m", "gunicorn", "-w", "4", "-b", "0.0.0.0:8080", "app:app"]