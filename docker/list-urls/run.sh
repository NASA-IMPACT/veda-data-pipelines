#!/bin/bash
# EXAMPLE:
# ./run.sh he5\" \
#   https://acdisc.gesdisc.eosdis.nasa.gov/data/Aura_OMI_Level3/OMNO2d.003/2020/ \
#   3 \
#   s3://omi-no2-nasa/validation/urls.txt
# or for appending:
# 
# for year in 2004 2005 2006 2007 2008 2009 2010 2011 2012 2013 2014 2015 2016
# do
#   ./run.sh he5\" \
#     https://acdisc.gesdisc.eosdis.nasa.gov/data/Aura_OMI_Level3/OMNO2d.003/${year}/ \
#     3 \
#     s3://omi-no2-nasa/urls.txt
# done
#
# ./run.sh 2020 \
#   https://e4ftl01.cr.usgs.gov/MOTA/MCD19A2.006/ \
#   5 \
#   s3://modis-aod-nasa/validation/directories.txt
# ./run.sh 2020 \
#   https://e4ftl01.cr.usgs.gov/MOLT/MOD13Q1.006/ \
#   5 \
#   s3://modis-vi-nasa/validation/MOD13Q1.006/directories.txt
# Generate a list of URLs with suffix $LINK_FINDER from $PARENT_DIRECTORY and write the result as a file
# `urls.txt` to $AWS_S3_PATH
LINK_FINDER=$1
PARENT_DIRECTORY=$2
AWK_ARG=$3
AWS_S3_PATH=$4

wget -e robots=off --force-html -O - $PARENT_DIRECTORY | \
  grep ${LINK_FINDER} | awk '{ print $'$AWK_ARG' }' | sed -e 's/.*href=['"'"'"]//' -e 's/["'"'"'].*$//' > filenames.txt

# Form complete urls from parent directory and filename
cat filenames.txt | while read line; do echo ${PARENT_DIRECTORY}$line ; done >> urls.txt

echo "Done generating urls.txt"
aws s3 cp urls.txt $AWS_S3_PATH --acl public-read

