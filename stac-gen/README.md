This docker image queries CMR for metadata associated with a granule, creates a STAC Item and then inserts it into a remote database.

```bash
docker build -t stac-gen .
# Currently runs an example for OMI Ozone
docker run --env STAC_DB_USER=<user> --env STAC_DB_PASSWORD=<pw> --env STAC_DB_HOST=<host> stac-gen python -m handler
```

Example Input:
```
{
  "collection": "OMDOAO3e",
  "s3_filename": "s3://climatedashboard-data/OMDOAO3e/OMI-Aura_L3-OMDOAO3e_2022m0120_v003-2022m0122t021759.he5.tif",
  "granule_id": "G2205784904-GES_DISC",
}
```
