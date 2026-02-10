FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml setup.py README.md /app/
COPY blockchain_core /app/blockchain_core
COPY business_logic /app/business_logic
COPY security /app/security
COPY network /app/network
COPY examples /app/examples
COPY pki_setup.py /app/

RUN pip install --no-cache-dir .

ENTRYPOINT ["python", "examples/network_demo.py"]
