#!/bin/bash
export SRC_URL=$1
wget $SRC_URL

FILENAME=`url="${SOURCE_URL}"; echo "${url##*/}"`
echo 'FILENAME: '$FILENAME

python3 handler.py $FILENAME
