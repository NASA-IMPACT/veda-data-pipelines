# covid-data-pipeline

List URLS of files from a provider.

```
./run.sh he5 \
  https://acdisc.gesdisc.eosdis.nasa.gov/data/Aura_OMI_Level3/OMNO2d.003/2020/ \
  s3://omi-no2-nasa/validation
```

## Build and Test

```bash
export DOCKER_TAG=list-urls
docker build --tag $DOCKER_TAG:latest .
docker run -it list-urls ./run.sh he5 \
  https://acdisc.gesdisc.eosdis.nasa.gov/data/Aura_OMI_Level3/OMNO2d.003/2020/ \
  s3://omi-no2-nasa/validation
```

## Deploy and Run on AWS

### Pushing to ECR

```bash
export AWS_PROFILE=XXX
export AWS_ACCOUNT_ID=XXX
export AWS_REGION=XXX
$(aws ecr get-login --no-include-email --region $AWS_REGION)
docker tag $DOCKER_TAG:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$DOCKER_TAG:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$DOCKER_TAG:latest
```
