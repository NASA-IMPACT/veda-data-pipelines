#!/bin/bash

# RUN IN BATCH
if [[ -n $AWS_BATCH_JOB_ARRAY_INDEX ]]
then
  # S3 bucket and path to read urls from and write COGs to
  # TODO example shows filepath as initial input
  AWS_S3_PATH=$1

  # Get list of urls
  aws s3 cp $AWS_S3_PATH/s3-urls.txt .

  LINE_NUMBER=$(($AWS_BATCH_JOB_ARRAY_INDEX + 1))
  SRC_URL=`sed -n ''$LINE_NUMBER','$LINE_NUMBER'p' < s3-urls.txt`
elif [[ -n $1 ]]
then
  # Run for a specific url
  SRC_URL=$1
else
  echo 'No url parameter, please pass a URL for testing'
  exit 1
fi

FILENAME=`url="${SRC_URL}"; echo "${url##*/}"`
echo 'Generating COG from '$FILENAME
aws s3 cp $SRC_URL $FILENAME
aws s3 cp ${SRC_URL}.hdr ${FILENAME}.hdr

COG_FILENAME=$(python handler.py -f $FILENAME)
echo "cog FILENAME $COG_FILENAME"

if [[ -n $AWS_S3_PATH ]]
then
  echo "Writing ${COG_FILENAME} to $AWS_S3_PATH"
  aws s3 cp $COG_FILENAME $AWS_S3_PATH/$COG_FILENAME
fi
