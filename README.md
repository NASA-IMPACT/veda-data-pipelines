# covid-data-pipeline

## Build and Test

```bash
export DOCKER_TAG=hdf-to-cog
docker build --tag $DOCKER_TAG:latest .
docker run -t hdf-to-cog -itd $DOCKER_TAG:latest
docker exec -it hdf-to-cog ./run.sh https://avdc.gsfc.nasa.gov/pub/data/satellite/Aura/OMI/V03/L3/OMNO2d_HR/OMNO2d_HRD/2020/2020_01_01_NO2TropCS30_Col3_V4.hdf5
```

## Deploy and Run on AWS

### Pushing to ECR

```bash
export AWS_ACCOUNT_ID=XXX
export AWS_REGION=XXX
$(aws ecr get-login --no-include-email --region $AWS_REGION)
docker tag $DOCKER_TAG:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$DOCKER_TAG:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$DOCKER_TAG:latest
```
