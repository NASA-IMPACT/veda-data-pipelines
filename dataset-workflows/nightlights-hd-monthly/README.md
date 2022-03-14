## Black Marble High Definition Nightlights Monthly Dataset
For expediency, the Black Marble High Definition Nightlights Monthly dataset from the covid-19 dashboard was ingested into the [delta-backend](https://github.com/NASA-IMPACT/delta-backend) STAC catalog using one-off python scripts. These scripts are included here for reproducibility and to support future pipeline development.

## Contents
**`nightlights-hd-monthly.py`**

Python code to ingests the full covid-19 Black Marble High Definition Nightlights dataset into a target PgSTAC database using [pypgstac](https://github.com/stac-utils/pgstac#pypgstac) from a laptop.
1. The collection json object is flattened to an ndjson array and inserted into pgstac.
2. A boto3 search is used to identify all COG datasets matching a bucket key pattern.
3. STAC records are created with raster and projection information for each matching COG using [rio-stac](http://devseed.com/rio-stac/api/rio_stac/stac/#create_stac_item).
4. An ndarray of all new item records is ingested to pgstac using pypgstac.
5. Finally, the update_default_summaries dashboard extension function in the pgstac database is executed to update the collection record with dynamic item datetime and default COG raster statistic summaries.


## Requirements
```
boto3
pypgstac
psycopg[binary]
pystac
rio_stac
tqdm
```

## Set-up
Parameters are hard coded in these one-off load routines; here are the parameters that need to be set.

1. Confirm that the collection json defined in the file is correct
   - `item_assets`, `dashboard:is_periodic`, and `dashboad:time_density` are required properties to generate collection statistics.
2. Confirm that the S3 bucket and prefix are correct
3. Set AWS secret key name (or ARN) to lookup database credentials in target environment
4. [Optional] Set AWS profile name if not using default profile
5. Run once with `dry_run=True` and verify the ndjson outputs for accuracy. When dry_run is false, the records will be published to the target database and the local files will be removed.
