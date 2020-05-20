#!/bin/bash
# EXAMPLE:
# ./run.sh he5 \
#   https://acdisc.gesdisc.eosdis.nasa.gov/data/Aura_OMI_Level3/OMNO2d.003/2020/ \
#   s3://omi-no2-nasa/validation
# Generate a list of URLs with suffix $FILE_SUFFIX from $PARENT_DIRECTORY and write the result as a file
# `urls.txt` to $AWS_S3_PATH
FILE_SUFFIX=$1
PARENT_DIRECTORY=$2
AWS_S3_PATH=$3

wget -e robots=off --force-html -O - $PARENT_DIRECTORY | \
  grep ${FILE_SUFFIX}\" | awk '{ print $3 }' | sed -e 's/.*href=['"'"'"]//' -e 's/["'"'"'].*$//' > filenames.txt

# Form complete urls from parent directory and filename
cat filenames.txt | while read line; do echo ${PARENT_DIRECTORY}$line ; done > urls.txt

echo "Done generating urls.txt"
aws s3 cp urls.txt $AWS_S3_PATH/urls.txt --acl public-read

