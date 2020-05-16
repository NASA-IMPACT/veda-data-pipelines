#!/bin/bash

if [[ -z $AWS_PROFILE ]]; then
  echo 'Please set AWS_PROFILE'
  exit 1
fi

if [[ -n $1 ]]; then
  COLLECTION=$1
else
  echo 'Please pass a collection name, such as "OMNO2d_HRM"'
  exit 1
fi

DATETIME=`date '+%Y%m%d-%H%M%S'`
JOB_NAME="nc-to-cog_${COLLECTION}_${DATETIME}"
echo "Executing job ${JOB_NAME}"
if [[ -n $2 ]]
then
  SIZE=$2
else
  SIZE=2
fi

aws2 batch submit-job \
  --job-name $JOB_NAME \
  --job-queue default-job-queue \
  --array-properties size=$SIZE \
  --job-definition nc_to_cog_batch_job_def \
  --container-overrides command=./home/run-cog-convert.sh,s3://covid-eo-data/$COLLECTION

