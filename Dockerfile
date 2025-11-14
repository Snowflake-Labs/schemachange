FROM python:3.12

RUN pip install schemachange

ENTRYPOINT schemachange
