# Dockerfile

FROM python:3-onbuild

COPY spifi_server /spifi_server

COPY spifiapi /spifiapi

COPY requirements.txt /requirements.txt

COPY manage.py /manage.py

COPY start.sh /start.sh

EXPOSE 80

CMD "./start.sh"
