#!/bin/bash

# Run in batch
if [[ -n $AWS_BATCH_JOB_ARRAY_INDEX ]]
then
  # S3 bucket and path to read urls from and write COGs to
  AWS_S3_PATH=$1

  # Get list of parent paths
  aws s3 cp $AWS_S3_PATH/directories.txt .

  LINE_NUMBER=$(($AWS_BATCH_JOB_ARRAY_INDEX + 1))
  PARENT_DIRECTORY=`sed -n ''$LINE_NUMBER','$LINE_NUMBER'p' < directories.txt`
elif [[ -n $1 ]]
then
  # For local testing or testing in a "single" type batch job
  # we can run for a specific url ($1)
  # limit the number of files to mosaic ($2)
  # upload the result to AWS_S3_PATH ($3)
  PARENT_DIRECTORY=$1
  FILES_LIMIT=$2
  AWS_S3_PATH=$3
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
echo "$FILENAMES" | while read filename
do
  echo 'Generating COG from '$filename
  python handler.py -f data/$filename
done

# Merge + create COG
output_filename=`echo $(basename $PARENT_DIRECTORY).tif`
ls data/*.tif > my_list_of_cog.txt
gdalbuildvrt cog.vrt -input_file_list my_list_of_cog.txt
rio cogeo create cog.vrt $output_filename --co blockxsize=256 --co blockysize=256
rio cogeo validate $output_filename

if [[ -n $AWS_S3_PATH ]]
then
  echo "Writing ${output_filename}.tif to $AWS_S3_PATH"
  aws s3 cp $output_filename $AWS_S3_PATH/$output_filename --acl public-read
fi

