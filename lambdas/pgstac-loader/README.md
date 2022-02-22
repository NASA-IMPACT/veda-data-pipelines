# PG STAC Loader

Test with python locally (uses example data in [hlss30_stac_example.ndjson](./hlss30_stac_example.ndjson))

```bash
python -m handler
```

Build and test the docker image:

```bash
# From the root of this repository
docker build -t pgstac_loader -f lambdas/pgstac-loader/Dockerfile .
export SECRET_NAME=delta-backend-dev/pgstac/XXX
# TODO (aimee): This isn't currently working because we are getting an import error for boto3
# docker run --env "SECRET_NAME=$SECRET_NAME" python -m handler
```
