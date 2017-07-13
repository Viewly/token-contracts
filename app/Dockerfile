FROM python:3.5.3
MAINTAINER furion <_@furion.me>

COPY . /src
WORKDIR /src

RUN pip install -r requirements.txt

ENV PRODUCTION yes
ENV FLASK_HOST 0.0.0.0

EXPOSE 5000

CMD ["python", "src/mentions-app.py"]
