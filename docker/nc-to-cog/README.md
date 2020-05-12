# covid-data-pipeline

## Build and Test

```bash
docker build .
docker run -itd -t cog-convert /bin/bash
docker exec -it <container_id> /home/run-cog-convert.sh https://avdc.gsfc.nasa.gov/pub/data/satellite/Aura/OMI/V03/L3/OMNO2d_HR/OMNO2d_HRM/OMI_trno2_0.10x0.10_200410_Col3_V4.nc
```