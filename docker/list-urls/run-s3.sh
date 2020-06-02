#!/bin/bash
# EXAMPLE:
# ./run-s3.sh s3://covid-eo-data/viirs/source_data/COVID19_Dashboard_BMHD/ .tif s3://covid-eo-data/BMHD_30M_MONTHLY
S3_SOURCE=$1
FILE_SUFFIX=$2
S3_DEST=$3

aws2 s3 ls $S3_SOURCE | grep $2 | awk '{ print $4 }' > filenames.txt

# Form complete urls from parent directory and filename
export URLS_FILENAME=s3-urls.txt
cat filenames.txt | while read line; do echo ${S3_SOURCE}$line ; done > $URLS_FILENAME

echo "Done generating ${URLS_FILENAME}"
aws2 s3 cp s3-urls.txt $S3_DEST/$URLS_FILENAME

