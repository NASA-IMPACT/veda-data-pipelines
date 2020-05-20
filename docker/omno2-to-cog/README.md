# omno2-to-cog docker

Code for converting NetCDF and HDF OMI NO2 data to Cloud-Optimized GeoTiff.

This code currently works for the following OMI NO2 colletions:
* [OMNO2d: OMI/Aura NO2 Cloud-Screened Total and Tropospheric Column L3 Global Gridded 0.25 degree x 0.25 degree V3](https://acdisc.gesdisc.eosdis.nasa.gov/data/Aura_OMI_Level3/OMNO2d.003/)
* 


## Test handler.py

```bash
wget -O OMI_trno2_0.10x0.10_202003_Col3_V4.nc \
  https://avdc.gsfc.nasa.gov/pub/data/satellite/Aura/OMI/V03/L3/OMNO2d_HR/OMNO2d_HRM/OMI_trno2_0.10x0.10_202003_Col3_V4.nc
python OMNO2d_HR/handler.py -f OMI_trno2_0.10x0.10_202003_Col3_V4.nc
rio viz OMI_trno2_0.10x0.10_202003_Col3_V4.nc.tif
```

## Build and Test 

Note: This requires you have a valid urs.earthdata.gov username and password and
have them set as environment variables `EARTHDATA_USERNAME` and
`EARTHDATA_PASSWORD`.

```bash
./build.sh

# For 0.1 degree daily + monthly Aura Validation products
docker run -it $DOCKER_TAG:latest \
  ./run-cog-convert.sh OMNO2d_HR \
  https://avdc.gsfc.nasa.gov/pub/data/satellite/Aura/OMI/V03/L3/OMNO2d_HR/OMNO2d_HRM/OMI_trno2_0.10x0.10_200410_Col3_V4.nc

# For 0.25 degree official GES DISC daily product
docker run -it $DOCKER_TAG:latest \
  ./run-cog-convert.sh OMNO2d.003 \
  https://acdisc.gesdisc.eosdis.nasa.gov/data/Aura_OMI_Level3/OMNO2d.003/2020/OMI-Aura_L3-OMNO2d_2020m0101_v003-2020m0330t173100.he5
```

## Deploy docker image to AWS Elastic Container Registry (ECR)

```bash
export AWS_PROFILE=XXX
export AWS_ACCOUNT_ID=XXX
export AWS_REGION=XXX
$(aws ecr get-login --no-include-email --region $AWS_REGION)
docker tag $DOCKER_TAG:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$DOCKER_TAG:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$DOCKER_TAG:latest
```

