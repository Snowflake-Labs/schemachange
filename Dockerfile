FROM python:3.7

RUN pip install snowchange==0.0.2

ENTRYPOINT snowchange
