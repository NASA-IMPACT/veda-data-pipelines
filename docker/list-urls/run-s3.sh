#!/bin/bash
# EXAMPLE:
# ./run-s3.sh s3://covid-eo-data viirs/source_data/COVID19_Dashboard_BMHD/ .tif s3://covid-eo-data/BMHD_30M_MONTHLY
# FIXMES
# - first result is a directory
# - OMIT matches in grep, just better regex matching
# ./run-s3.sh s3://covid-eo-data viirs/source_data/VNP46A2_V011/ "-v .hdr" s3://covid-eo-data/BM_500M_DAILY
S3_SRC_BUCKET=$1
S3_SRC_DIR=$2
FILE_SUFFIX=$3
S3_DEST=$4

aws2 s3 ls $S3_SRC_BUCKET/$S3_SRC_DIR --recursive | grep ${FILE_SUFFIX} | awk '{ print $4 }' > filenames.txt

# Form complete urls from parent directory and filename
export URLS_FILENAME=s3-urls.txt
cat filenames.txt | while read line; do echo ${S3_SRC_BUCKET}/$line ; done > $URLS_FILENAME

echo "Done generating ${URLS_FILENAME}"
aws2 s3 cp s3-urls.txt $S3_DEST/$URLS_FILENAME
cat s3-urls.txt
