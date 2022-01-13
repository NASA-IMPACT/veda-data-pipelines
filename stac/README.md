Docker to query CMR for granules associated with a given collection and temporal range.

```bash
docker build -t cmr-query .
# Currently runs an example for OMI Ozone
docker run cmr-query python -m handler
```