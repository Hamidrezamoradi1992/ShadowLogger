FROM python:3.12-slim as base

LABEL maintainer="hamedreza1992@gmail.com"


# set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1


WORKDIR /usr/src/app

COPY requirements.txt .

RUN apt-get update
RUN apt-get install gettext -y
RUN apt-get install gdal-bin -y
RUN apt-get clean
RUN rm -rf /var/lib/apt/lists/*

RUN pip3 install --upgrade pip && pip3 install -r requirements.txt



COPY ./core .