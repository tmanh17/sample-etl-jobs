FROM python:3.7-alpine3.9
RUN apk add tzdata \
&& cp /usr/share/zoneinfo/Asia/Ho_Chi_Minh /etc/localtime \
&& echo "Asia/Ho_Chi_Minh" >  /etc/timezone \
&& apk del tzdata

COPY requirements.txt /

RUN pip3 install -U pip \
    && pip3 install -r /requirements.txt

COPY app /app
RUN chmod +x /app/main.py
WORKDIR /app
