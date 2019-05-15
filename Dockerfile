FROM python:3.6
MAINTAINER bobbie <dev.bobbie@gmail.com>

COPY ./bookspider /bookspider/bookspider
COPY ./requirements.txt /bookspider/
COPY scrapy.cfg /bookspider/
WORKDIR /bookspider/
# 安装依赖
RUN pip install --no-cache-dir --trusted-host mirrors.aliyun.com -i http://mirrors.aliyun.com/pypi/simple/ -r requirements.txt

COPY main.py /bookspider/

ENV TIME_ZONE=Asia/Shanghai
RUN echo "${TIME_ZONE}" > /etc/timezone \
    && ln -sf /usr/share/zoneinfo/${TIME_ZONE} /etc/localtime


