FROM python:3.12-slim

ARG SCHEMACHANGE_VERSION=""

RUN if [ -n "$SCHEMACHANGE_VERSION" ]; then \
        pip install --no-cache-dir "schemachange==${SCHEMACHANGE_VERSION}"; \
    else \
        pip install --no-cache-dir schemachange; \
    fi

ENTRYPOINT ["schemachange"]
