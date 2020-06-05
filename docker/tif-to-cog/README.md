# tif-to-cog docker

Too simple?! Convert geotiff to cloud-optimized geotiff using rio-cogeo.

Also modifies the filename to make the date more template friendly.

## Test run.sh

```bash
./run.sh s3://covid-eo-data/viirs/source_data/COVID19_Dashboard_BMHD/BMHD_Beijing_China_VNP46A2_Jan2020.tif
rio cogeo validate BMHD_Beijing_China_VNP46A2_Jan2020_cog.tif
```

## Build and Test tif-to-cog docker

```bash
./build.sh
docker run -it $DOCKER_TAG:latest ./run.sh s3://covid-eo-data/viirs/source_data/COVID19_Dashboard_BMHD/BMHD_Beijing_China_VNP46A2_Jan2020.tif
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

