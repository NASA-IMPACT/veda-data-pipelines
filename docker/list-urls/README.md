# List files scripts

Scripts for generating lists of files to process and upload that list to S3. These lists are used in AWS Batch Array jobs where each child job can pick from the list based off its `AWS_BATCH_JOB_ARRAY_INDEX` (and then the whole list can be processed in parallel). `AWS_BATCH_JOB_ARRAY_INDEX` is AWS Batch array job environment variable, learn more here: [AWS Docs: Array Jobs](https://docs.aws.amazon.com/batch/latest/userguide/array_jobs.html).

* `run.sh` creates a list of URLs for a given parent directory and uploads the list to S3.
* `list-s3-files.sh` creates a list of S3 URLs using `aws s3 ls`.

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
docker run -it $DOCKER_TAG ./run.sh he5 \
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
