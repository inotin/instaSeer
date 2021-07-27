# syntax=docker/dockerfile:1
FROM python:3.7.11-alpine
WORKDIR /instaseer
COPY requirements.txt requirements.txt
RUN cat requirements.txt | xargs -n 1 pip install
COPY . .
ENTRYPOINT ["python3.7"]
