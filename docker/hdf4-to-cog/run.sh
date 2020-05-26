#!/bin/bash
#
# `run.sh` is specific to MODIS HDF4 collections which call for global
# mosaicing A parent directory is passed in (unless running in AWS Batch mode)
# and all files within a parent directory are from the same date but different
# bounding boxes A tif is generated from each file using `handler.py` and then
# merged into a global cloud-optimized geotiff.
# 
if [[ -n $1 ]]
then
  COLLECTION=$1
else
  echo 'No collection parameter, please pass a collection name to indicate which
  handler to call.'
  exit 1
fi

# Run in batch
if [[ -n $AWS_BATCH_JOB_ARRAY_INDEX ]]
then
  # S3 bucket and path to read urls from and write COGs to
  AWS_S3_PATH=$2

  # Get list of parent paths
  aws s3 cp $AWS_S3_PATH/directories.txt .

  LINE_NUMBER=$(($AWS_BATCH_JOB_ARRAY_INDEX + 1))
  PARENT_DIRECTORY=`sed -n ''$LINE_NUMBER','$LINE_NUMBER'p' < directories.txt`
elif [[ -n $1 ]]
then
  # For local testing or testing in a "single" type batch job
  # we can run for a specific parent url ($2)
  # limit the number of files to mosaic ($2)
  # upload the result to AWS_S3_PATH ($3)
  PARENT_DIRECTORY=$2
  FILES_LIMIT=$3
  AWS_S3_PATH=$4
else
  echo 'No url parameter, please pass a URL for testing'
  exit 1
fi

unset GDAL_DATA
# Generate a list of filenames for this day
wget -e robots=off --force-html -O - $PARENT_DIRECTORY | \
  grep ".hdf\"" | awk '{ print $6 }' | sed 's/.*href="\([^ ]*\.hdf\)".*/\1/' > filenames.txt


# Form complete urls from parent directory and filename
if [[ -n $FILES_LIMIT ]]
then
  FILENAMES=`sed -n '1,'$FILES_LIMIT'p' < filenames.txt`
else
  FILENAMES=`cat filenames.txt`
fi

echo "$FILENAMES" | while read line; do echo ${PARENT_DIRECTORY}$line ; done > urls.txt

# Download all the files in parallel
xargs -n 1 -P 10 wget -P data/ \
  --load-cookies ~/.urs_cookies \
  --save-cookies ~/.urs_cookies \
  --auth-no-challenge=on \
  --keep-session-cookies \
  --content-disposition < urls.txt

# Generate a TIF for each file
echo "${FILENAMES}" | xargs -n 1 -P 10 python handler.py --directory data/ -c $COLLECTION -f

# Merge + create COG
output_filename=`echo $(basename $PARENT_DIRECTORY).tif`
ls data/*.tif > my_list_of_cog.txt
gdalbuildvrt cog.vrt -input_file_list my_list_of_cog.txt
# FIXME - Only known solution to adding band names
if [[ "$COLLECTION" == "AOD" ]]; then
  rio edit-info cog.vrt --bidx 1 --description Optical_Depth_047
  rio edit-info cog.vrt --bidx 2 --description Optical_Depth_055
elif [[ "$COLLECTION" == "VI" ]]; then
  rio edit-info cog.vrt --bidx 1 --description '250m 16 days NDVI'
  rio edit-info cog.vrt --bidx 2 --description '250m 16 days EVI'
elif [[ "$COLLECTION" == "VI_500M" ]]; then
  rio edit-info cog.vrt --bidx 1 --description '500m 16 days NDVI'
  rio edit-info cog.vrt --bidx 2 --description '500m 16 days EVI'
elif [[ "$COLLECTION" == "VI_MONTHLY" ]]; then
  rio edit-info cog.vrt --bidx 1 --description '1 km monthly NDVI'
  rio edit-info cog.vrt --bidx 2 --description '1 km monthly EVI'
else
  echo 'No band names for '$COLLECTION
fi

rio cogeo create cog.vrt $output_filename --co blockxsize=256 --co blockysize=256
rio cogeo validate $output_filename

if [[ -n $AWS_S3_PATH ]]
then
  echo "Writing ${output_filename} to $AWS_S3_PATH"
  aws s3 cp $output_filename $AWS_S3_PATH/$output_filename --acl public-read
fi

