FROM python:3.12-slim

LABEL maintainer="Satyabrata <satyabrata.7059@gmail.com>"

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 