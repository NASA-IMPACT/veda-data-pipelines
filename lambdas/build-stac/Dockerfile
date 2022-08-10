FROM python:3.9-slim-bullseye

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
