# HDF5 to COG

```bash
# Build it
export DOCKER_TAG=hdf5-to-cog
docker build -t $DOCKER_TAG:latest .
```

```bash
# Test it
docker run -it \
  --env EARTHDATA_USERNAME=$USERNAME --env EARTHDATA_PASSWORD=$PASSWORD \
  hdf5-to-cog:latest \
  python run.py \
  -c GPM_3IMERGDF \
  -f https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGDF.06/2000/06/3B-DAY.MS.MRG.3IMERG.20000601-S000000-E235959.V06.nc4
```