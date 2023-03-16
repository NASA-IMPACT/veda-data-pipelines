FROM --platform=linux/amd64 python:3.9-slim-bullseye as production

WORKDIR /app

# Install Python dependencies
RUN pip install --upgrade pip
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
RUN rm requirements.txt

COPY handler.py .
COPY utils ./utils

# Precompile
RUN python -m compileall .

# Test target
FROM production AS test

COPY requirements-test.txt requirements-test.txt
RUN pip install -r requirements-test.txt
RUN rm requirements-test.txt

COPY tests ./tests
CMD ["pytest", "tests"]
