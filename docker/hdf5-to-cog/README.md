# HDF5 to COG

```bash
# Build it
export DOCKER_TAG=hdf5-to-cog
docker build -t $DOCKER_TAG:latest .
```

```bash
# Test it
docker run -it \
  --env SSM_PREFIX=cloud-optimized-dp \
  --env AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
  --env AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
  hdf5-to-cog:latest \
  python run.py \
  -c GPM_3IMERGM \
  -f https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGM.06/2020/3B-MO.MS.MRG.3IMERG.20200501-S000000-E235959.05.V06B.HDF5
```