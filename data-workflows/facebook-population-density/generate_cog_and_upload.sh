#!/bin/bash

# download .vrt file (which point to data in both `v1/` and `v1.5/` so we have to download both
aws s3 cp s3://dataforgood-fb-data/hrsl-cogs/hrsl_general/hrsl_general-latest.vrt . 

# download datafiles
aws s3 sync s3://dataforgood-fb-data/hrsl-cogs/hrsl_general/v1 ./v1
aws s3 sync s3://dataforgood-fb-data/hrsl-cogs/hrsl_general/v1.5 ./v1.5

# create gobal tif
GDAL_DISABLE_READDIR_ON_OPEN=EMPTY_DIR rio cogeo create ./hrsl_general-latest.vrt hrsl_general_latest_global_cog.tif --allow-intermediate-compression --blocksize 512 --overview-blocksize 512

# copy the created tif to the climate dashboard data bucket
aws s3 cp ./hrsl_general_latest_global_cog.tif  s3://climatedashboard-data/facebook_population_density/hrsl_general_latest_global_cog.tif
