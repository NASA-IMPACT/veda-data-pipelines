Docker to query CMR for granules associated with a given collection and temporal range.

```bash
docker build -t stac-gen .
# Currently runs an example for OMI Ozone
docker run --env USER=<user> --env PASSWORD=<pw> --env HOST=<host> stac-gen python -m handler
```
