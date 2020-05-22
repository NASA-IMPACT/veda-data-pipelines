# hdf4-to-cog docker

Code for converting HDF4 to Cloud-Optimized GeoTiff. 

## Test handler.py

```bash
wget -O MCD19A2.A2020134.h35v10.006.2020136043337.hdf https://e4ftl01.cr.usgs.gov/MOTA/MCD19A2.006/2020.05.13/MCD19A2.A2020134.h35v10.006.2020136043337.hdf
python handler.py -f MCD19A2.A2020134.h35v10.006.2020136043337.hdf
rio cogeo validate MCD19A2.A2020134.h35v10.006.2020136043337.hdf.tif
```

## Build and Test hdf4-to-cog docker

Note: This requires you have a valid urs.earthdata.gov username and password and
have them set as environment variables `EARTHDATA_USERNAME` and
`EARTHDATA_PASSWORD`.

```bash
./build.sh
docker run -it $DOCKER_TAG:latest python handler.py -f MCD19A2.A2020134.h35v10.006.2020136043337.hdf
docker run -it $DOCKER_TAG:latest ./run.sh https://e4ftl01.cr.usgs.gov/MOTA/MCD19A2.006/2020.05.13/
```

## Deploy docker image to AWS Elastic Container Registry (ECR)

```bash
export AWS_PROFILE=xxx
export AWS_ACCOUNT_ID=xxx
export AWS_REGION=us-east-1
$(aws ecr get-login --no-include-email --region $AWS_REGION)
docker tag $DOCKER_TAG:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$DOCKER_TAG:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$DOCKER_TAG:latest
```

