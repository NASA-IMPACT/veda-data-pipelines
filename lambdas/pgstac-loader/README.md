# PG STAC Loader

```bash
# From the root of this repository
docker build -t pgstac_loader -f lambdas/pgstac-loader/Dockerfile .
export SECRET_NAME=delta-backend-dev/pgstac/XXX
docker run --env "SECRET_NAME=$SECRET_NAME" python -m handler.py
```