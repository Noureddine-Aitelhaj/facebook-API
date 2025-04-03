FROM python:3.9-slim

WORKDIR /app

# Install git for cloning the Facebook repository
RUN apt-update && apt-get install -y git

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]
