## ndJSON builder function

Handler for a lambda which receieves messages from a SQSEventSource trigger containing a list of STAC JSON files. Fetch and build the data into ndJSON files, upload to 

```bash
docker build -t ndjson-builder .
# Runs an example in handler.py
docker run --env BUCKET=XXX --env QUEUE_URL=XXX ndjson-builder python -m handler 
```

