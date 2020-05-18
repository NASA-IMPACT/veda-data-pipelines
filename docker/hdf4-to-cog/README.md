# hdf4-to-cog docker

Code for converting HDF4 to Cloud-Optimized GeoTiff. 

## Test handler.py

```bash
wget -O MCD19A2.A2020134.h35v10.006.2020136043337.hdf https://e4ftl01.cr.usgs.gov/MOTA/MCD19A2.006/2020.05.13/MCD19A2.A2020134.h35v10.006.2020136043337.hdf
python handler.py
rio cogeo validate MCD19A2.A2020134.h35v10.006.2020136043337.hdf
```

## Build and Test hdf4-to-cog docker

```bash
export DOCKER_TAG=hdf4-to-cog
docker build -t $DOCKER_TAG:latest .
docker run -it $DOCKER_TAG:latest python handler.py 
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

