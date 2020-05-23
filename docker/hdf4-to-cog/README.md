# hdf4-to-cog docker

Code for converting HDF4 to Cloud-Optimized GeoTiff. 

## Test handler.py

### For AOD data

```bash
wget -O MCD19A2.A2020134.h35v10.006.2020136043337.hdf https://e4ftl01.cr.usgs.gov/MOTA/MCD19A2.006/2020.05.13/MCD19A2.A2020134.h35v10.006.2020136043337.hdf
python handler.py -f MCD19A2.A2020134.h35v10.006.2020136043337.hdf --cog --collection AOD
rio cogeo validate MCD19A2.A2020134.h35v10.006.2020136043337_cog.tif
```

Note: You can create a regular tif or a cloud-optimized tif dependent on the
addition of the `--cog` suffix when calling `python handler.py`.

### For VI data

```bash
python handler.py -f MOD13Q1.A2020113.h03v11.006.2020130012353.hdf --cog -c VI
```

## Build and Test hdf4-to-cog docker

Note: This requires you have a valid urs.earthdata.gov username and password and
have them set as environment variables `EARTHDATA_USERNAME` and
`EARTHDATA_PASSWORD`.

Build:

```bash
./build.sh
```

Test run for AOD:

```bash
# Test run for generating a global mosaic for 10 files
docker run -it $DOCKER_TAG:latest ./run.sh AOD https://e4ftl01.cr.usgs.gov/MOTA/MCD19A2.006/2020.05.13/ 10
```

```bash
# Test run for generating a global mosaic for 10 files
docker run -it $DOCKER_TAG:latest ./run.sh VI https://e4ftl01.cr.usgs.gov/MOLT/MOD13Q1.006/2020.04.22/ 10
```

## Deploy docker image to AWS Elastic Container Registry (ECR)

```bash
export AWS_PROFILE=XXX
export AWS_ACCOUNT_ID=XXX
export AWS_REGION=XXX
$(aws2 ecr get-login --no-include-email --region $AWS_REGION)
docker tag $DOCKER_TAG:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$DOCKER_TAG:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$DOCKER_TAG:latest
```

