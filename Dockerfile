FROM python:3.9-alpine

LABEL maintainer="bardin.petr@gmail.com"
LABEL version="0.1"

EXPOSE 8998

RUN mkdir /app
WORKDIR /app

RUN apk add wget

RUN pip install pipenv

ADD Pipfile .
ADD Pipfile.lock .

RUN pipenv install --system --deploy --ignore-pipfile

COPY autoopen /app

RUN wget https://file.bardinpa.ru/knn.bin

ENTRYPOINT ["python3", "autoopen/main.py"]