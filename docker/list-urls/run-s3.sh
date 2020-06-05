#!/bin/bash
# List all objects (recursively) in an S3 directory matching or excluding (grep -v) a substring
# Examples:
#
# Find all files including ".tif"
# ./run-s3.sh s3://covid-eo-data viirs/source_data/COVID19_Dashboard_BMHD/ .tif s3://covid-eo-data/BMHD_30M_MONTHLY
#
# Find all files which don't include ".hdr"
# This is useful when the processing script only requires one of multiple files.
# For example when processing an .img file also requires a complementary
# .img.hdr file, but the script only requires .img as an argument.
# ./run-s3.sh s3://covid-eo-data viirs/source_data/VNP46A2_V011/ "-v .hdr" s3://covid-eo-data/BM_500M_DAILY
S3_SRC_BUCKET=$1
S3_SRC_DIR=$2
LINK_FINDER=$3
S3_DEST=$4

aws s3 ls $S3_SRC_BUCKET/$S3_SRC_DIR/ --recursive | grep ${LINK_FINDER} | awk '{ print $4 }' > filenames.txt

# Form complete urls from parent directory and filename
export URLS_FILENAME=s3-urls.txt
cat filenames.txt | while read line; do echo ${S3_SRC_BUCKET}/$line ; done > $URLS_FILENAME

echo "Done generating ${URLS_FILENAME}"
aws s3 cp s3-urls.txt $S3_DEST/$URLS_FILENAME
cat s3-urls.txt
