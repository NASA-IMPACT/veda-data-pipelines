#!/bin/bash

# S3 bucket and path to read urls from and write COGs to
# TODO example shows filepath as initial input
AWS_S3_PATH=$1

# Determine which URL to fetch
if [[ -n $AWS_BATCH_JOB_ARRAY_INDEX ]]
then
  LINE_NUMBER=$(($AWS_BATCH_JOB_ARRAY_INDEX + 1))
  SRC_URL=`sed -n ''$LINE_NUMBER','$LINE_NUMBER'p' < urls.txt`
elif [[ -n $1 ]]
then
  # In case we pass a specific url
  SRC_URL=$1
else
  echo 'No url parameter, please pass a URL for testing'
  exit 1
fi
wget $SRC_URL

# Get list of urls
aws s3 cp s3://$AWS_S3_PATH/urls.txt .

FILENAME=`url="${SRC_URL}"; echo "${url##*/}"`
echo 'Generating COG from '$FILENAME

python3 /home/handler.py -f $FILENAME

aws s3 cp ${FILENAME}.cog.tif $AWS_S3_COG_LOCATION
