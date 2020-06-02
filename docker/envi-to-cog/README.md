# envi-to-cog docker

Convert .img and .img.hdr to cloud-optimized geotiff using rio-cogeo

## Test run.sh

```bash
./run.sh s3://covid-eo-data/viirs/source_data/VNP46A2_V011/h05v05/2020/001/VNP46A2_V011.h05v05.A2020001.5000.109.49_24.41_V30.img
rio cogeo validate VNP46A2_V011.h05v05.A2020001.5000.109.49_24.41_V30_cog.tif
```

## Build and Test envi-to-cog docker

```bash
./build.sh
# NOTE: This likely won't work locally because docker doesn't have AWS access
docker run -it $DOCKER_TAG:latest ./run.sh s3://covid-eo-data/viirs/source_data/VNP46A2_V011/h05v05/2020/001/VNP46A2_V011.h05v05.A2020001.5000.109.49_24.41_V30.img
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

