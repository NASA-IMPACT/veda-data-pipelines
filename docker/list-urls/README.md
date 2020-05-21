# covid-data-pipeline

Create a list of URLs for a given parent directory and upload them to S3. To be
used in combination with an AWS Batch Job which operates on the list in
parallel.

Example:

```bash
# ./run.sh <FILE SUFFIX> <PARENT DIRECTORY> <S3 PUT LOCATION>
./run.sh he5 \
  https://acdisc.gesdisc.eosdis.nasa.gov/data/Aura_OMI_Level3/OMNO2d.003/2020/ \
  s3://omi-no2-nasa/validation
```

Will generate a list of files ending in the suffix `.he5` and upload a
`urls.txt` file to s3://omi-no2-nasa/validation. Assumes access to put objects
in the S3 location.

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
