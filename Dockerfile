FROM python:3.7

RUN pip install snowchange

ENTRYPOINT snowchange
