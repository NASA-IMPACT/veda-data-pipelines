Docker to query CMR for granules associated with a given collection and temporal range.

```bash
docker build -t stac-gen .
# Currently runs an example for OMI Ozone
docker run --env STAC_DB_USER=<user> --env STAC_DB_PASSWORD=<pw> --env STAC_DB_HOST=<host> stac-gen python -m handler
```
