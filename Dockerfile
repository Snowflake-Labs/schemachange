FROM python:3.7

RUN pip install schemachange

ENTRYPOINT schemachange
