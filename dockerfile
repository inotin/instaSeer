# syntax=docker/dockerfile:1
FROM python:3.7-slim
WORKDIR /instaseer
COPY requirements.txt requirements.txt
RUN apt-get update ##[edited]
RUN apt-get install ffmpeg libsm6 libxext6  -y
RUN pip3 install --upgrade pip
RUN pip3 install Cython
RUN pip3 install scipy
RUN pip3 install scikit-learn
RUN cat requirements.txt | xargs -n 1 pip3 install
COPY . .
ENTRYPOINT ["python3", "-m", "instaSeer"]
