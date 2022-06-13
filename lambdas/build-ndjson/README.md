## Build ndjson function

Code intended to receive messages from an SQSEventSource trigger. Those messages contain a list of STAC JSON file URLs. Fetches and build the data into ndJSON files, upload to s3

```bash
docker build -t build-ndjson .
# Runs an example in handler.py
docker run --env BUCKET=XXX --env QUEUE_URL=XXX build-ndjson python -m handler 
```
