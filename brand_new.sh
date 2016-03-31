#!/bin/bash


apt-get install python-pip python-dev build-essential python-mysqldb
pip install sh

mkdir /webapps
mkdir /etc/nginx/global
cp restrictions.conf /etc/nginx/global
cp nginx /etc/logrotate.d/