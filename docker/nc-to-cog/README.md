# nc-to-cog docker

Code for converting NetCDF and HDF to Cloud-Optimized GeoTiff. 

## Test handler.py

```bash
wget -O OMI_trno2_0.10x0.10_202003_Col3_V4.nc https://avdc.gsfc.nasa.gov/pub/data/satellite/Aura/OMI/V03/L3/OMNO2d_HR/OMNO2d_HRM/OMI_trno2_0.10x0.10_202003_Col3_V4.nc
python handler.py -f OMI_trno2_0.10x0.10_202003_Col3_V4.nc
rio viz OMI_trno2_0.10x0.10_202003_Col3_V4.nc.tif
```

## Build and Test nc-to-cog docker

```bash
export DOCKER_TAG=nc-to-cog
docker build -t $DOCKER_TAG:latest .
docker run -it $DOCKER_TAG:latest /home/run-cog-convert.sh https://avdc.gsfc.nasa.gov/pub/data/satellite/Aura/OMI/V03/L3/OMNO2d_HR/OMNO2d_HRM/OMI_trno2_0.10x0.10_200410_Col3_V4.nc
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
