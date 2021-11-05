FROM python:3.9-alpine

LABEL maintainer="bardin.petr@gmail.com"
LABEL version="0.1"

EXPOSE 8998

RUN mkdir /app
WORKDIR /app

RUN apk add wget cmake make g++ gcc

RUN pip install pipenv

ADD Pipfile .
ADD Pipfile.lock .

RUN pipenv install --system --deploy --ignore-pipfile

RUN git clone https://github.com/davisking/dlib
RUN cd dlib; python setup.py install

COPY autoopen /app

RUN wget https://file.bardinpa.ru/knn.bin

ENTRYPOINT ["env PYTHONPATH=/app", "python3", "autoopen/main.py"]