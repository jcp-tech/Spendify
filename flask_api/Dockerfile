FROM python:3.10-slim

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

COPY . .

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libglib2.0-0 libsm6 libxext6 libxrender-dev && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080

# (Choose ONE of the following for CMD)
# 1. Use flask run (if installed and your requirements.txt has Flask)
# CMD ["flask", "run", "--host=0.0.0.0", "--port=8080"]

# 2. Run with Python directly (if your app runs with python main_api.py)
CMD ["python", "main_api.py"]

# 3. Use Gunicorn for production
# CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8080", "main_api:app"]