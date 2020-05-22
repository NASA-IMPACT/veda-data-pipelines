#!/bin/bash
export DOCKER_TAG=omno2-to-cog
docker build \
  --build-arg EARTHDATA_USERNAME=$EARTHDATA_USERNAME \
  --build-arg EARTHDATA_PASSWORD=$EARTHDATA_PASSWORD \
  -t $DOCKER_TAG:latest .

