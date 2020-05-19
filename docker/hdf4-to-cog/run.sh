#!/bin/bash

# RUN IN BATCH
if [[ -n $AWS_BATCH_JOB_ARRAY_INDEX ]]
then
  # S3 bucket and path to read urls from and write COGs to
  AWS_S3_PATH=$1

  # Get list of parent paths
  aws s3 cp $AWS_S3_PATH/parent_paths.txt .

  LINE_NUMBER=$(($AWS_BATCH_JOB_ARRAY_INDEX + 1))
  PARENT_DIRECTORY=`sed -n ''$LINE_NUMBER','$LINE_NUMBER'p' < urls.txt`
elif [[ -n $1 ]]
then
  # Run for a specific url
  PARENT_DIRECTORY=$1
  AWS_S3_PATH=$2
else
  echo 'No url parameter, please pass a URL for testing'
  exit 1
fi

unset GDAL_DATA
# Generate a list of filenames for this day
wget -e robots=off --force-html -O - $PARENT_DIRECTORY | \
  grep ".hdf\"" | awk '{ print $6 }' | sed 's/.*href="\([^ ]*\.hdf\)".*/\1/' > filenames.txt

# Form complete urls from parent directory and filename
cat filenames.txt | while read line; do echo ${PARENT_DIRECTORY}$line ; done > urls.txt
#head -n 50 filenames.txt | while read line; do echo ${PARENT_DIRECTORY}$line ; done > urls.txt

# Download all the files in parallel
xargs -n 1 -P 10 wget -P data/ \
  --load-cookies ~/.urs_cookies \
  --save-cookies ~/.urs_cookies \
  --auth-no-challenge=on \
  --keep-session-cookies \
  --content-disposition < urls.txt

# Generate a COG for each file
#head -n 50 filenames.txt | while read filename
cat filenames.txt | while read filename
do
  echo 'Generating COG from '$filename
  python handler.py -f data/$filename
done

# Merge + create COG
## Do we need the nodata value here?
output_filename=`echo $(basename $PARENT_DIRECTORY).tif`
ls data/*.tif | xargs rio merge -o merged.tif --overwrite
rio cogeo create merged.tif $output_filename
rio cogeo validate $output_filename

if [[ -n $AWS_S3_PATH ]]
then
  echo "Writing ${output_filename}.tif to $AWS_S3_PATH"
  aws s3 cp $output_filename $AWS_S3_PATH/$output_filename
fi

