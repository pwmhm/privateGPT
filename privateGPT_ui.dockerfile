FROM php:8.0.28-apache

RUN DEBIAN_FRONTEND=noninteractive
RUN apt-get -y update && apt-get install -y wget

RUN wget -O /var/www/html/jquery.min.js https://ajax.googleapis.com/ajax/libs/jquery/3.6.0/jquery.min.js

COPY ./ui /var/www/html