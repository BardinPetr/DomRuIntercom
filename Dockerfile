FROM jjanzic/docker-python3-opencv

LABEL maintainer="Bardin Petr <me@bardinpetr.ru>"
LABEL version="0.3"

RUN mkdir /app
WORKDIR /app

RUN apt update
RUN apt install -y libgl1

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8998

ENV PYTHONPATH="/app"
ENV DOCKER="1"

CMD ["python", "/app/autoopen/main.py"]