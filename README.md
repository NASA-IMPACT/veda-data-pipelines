# covid-data-pipeline

```bash
docker build --tag hdf-to-cog:latest .
docker run --name lambda -w /var/task --volume $(pwd)/:/local -itd hdf-to-cog:latest /bin/bash
docker exec -it lambda /bin/bash
./run.sh https://avdc.gsfc.nasa.gov/pub/data/satellite/Aura/OMI/V03/L3/OMNO2d_HR/OMNO2d_HRD/2020/2020_01_01_NO2TropCS30_Col3_V4.hdf5
```
