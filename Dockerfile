FROM python:3.11-slim

RUN mkdir /app
WORKDIR /app/
COPY . /app/

RUN pip install -r requirements.txt
CMD uvicorn "api.main:fastapi_app" --host 0.0.0.0 --port 8000
