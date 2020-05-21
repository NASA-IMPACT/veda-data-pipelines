#!/bin/bash

if [[ -n $1 ]]
then
  COLLECTION=$1
else
  echo 'No collection parameter, please pass a collection name to indicate which
  handler to call.'
  exit 1
fi

# RUN IN BATCH
if [[ -n $AWS_BATCH_JOB_ARRAY_INDEX ]]
then
  # S3 bucket and path to read urls from and write COGs to
  # TODO example shows filepath as initial input
  AWS_S3_PATH=$2

  # Get list of urls
  aws s3 cp $AWS_S3_PATH/urls.txt .

  LINE_NUMBER=$(($AWS_BATCH_JOB_ARRAY_INDEX + 1))
  SRC_URL=`sed -n ''$LINE_NUMBER','$LINE_NUMBER'p' < urls.txt`
elif [[ -n $2 ]]
then
  # Run for a specific url
  SRC_URL=$2
else
  echo 'No url parameter, please pass a URL for testing'
  exit 1
fi
wget \
  --load-cookies ~/.urs_cookies \
  --save-cookies ~/.urs_cookies \
  --auth-no-challenge=on \
  --keep-session-cookies $SRC_URL

FILENAME=`url="${SRC_URL}"; echo "${url##*/}"`
echo 'Generating COG from '$FILENAME

python3 /home/${COLLECTION}/handler.py -f $FILENAME

# the script replaces the original extension with "tif"
FILENAME_NO_EXT="${FILENAME%.*}"

if [[ -n $AWS_S3_PATH ]]
then
  echo "Writing ${FILENAME_NO_EXT}.tif to $AWS_S3_PATH"
  aws s3 cp ${FILENAME_NO_EXT}.tif $AWS_S3_PATH/${FILENAME_NO_EXT}.tif --acl public-read
fi

