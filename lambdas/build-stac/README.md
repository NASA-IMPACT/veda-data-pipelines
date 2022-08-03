## Build STAC function

Code intended to receive a message from an SQSEventSource trigger. The message contains data necessary to build a STAC Item. This STAC item is generated and written to a JSON file and uploaded to s3.

```bash
docker build -t build-stac .
# Runs an example in handler.py
docker run --env BUCKET=XXX build-stac python -m handler
```
