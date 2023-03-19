FROM python:3.8-slim

RUN cp -pv /etc/apt/sources.list /etc/apt/sources.list.bak
RUN sed -i -e 's/deb.debian.org/mirrors.ustc.edu.cn/g' -e 's/security.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list
RUN apt update
RUN apt-get update && apt-get install -y --no-install-recommends libgl1-mesa-glx
RUN apt-get install -y libglib2.0-dev libgomp1

WORKDIR /data/www

RUN pip config set global.index-url https://mirror.baidu.com/pypi/simple/
RUN pip install protobuf==3.20.0 paddlepaddle paddleocr flask
RUN pip install gunicorn gevent

COPY . .

CMD ["gunicorn", "main:app", "-c", "./gunicorn.conf.py"]