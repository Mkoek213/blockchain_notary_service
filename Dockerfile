FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml setup.py README.md /app/
COPY blockchain_core /app/blockchain_core
COPY business_logic /app/business_logic
COPY security /app/security
COPY network /app/network
COPY notary_service /app/notary_service
COPY examples /app/examples
COPY pki /app/pki
COPY pki_setup.py /app/

RUN pip install --no-cache-dir .

ENTRYPOINT ["python", "-m", "examples.ui_app"]
