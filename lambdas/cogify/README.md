# NetCDF4 / HDF5 to COG

🚧 WIP 🚧 Configurable module for converting NetCDF4 / HDF5 to COG.

At this time, just a few configurations have been made in `example.ini`.

Before running the commands below, make sure you `cd cogify/`.

## Testing

`handler.py` by default is using an example with OMI OAO3 dataset.

```bash
export EARTHDATA_USERNAME=xxx
export EARTHDATA_PASSWORD=XXX
# OR export AWS_PROFILE=xxx
export AWS_ACCESS_KEY_ID=XXX
export AWS_SECRET_ACCESS_KEY=XXX

docker build -t cogify .
# Runs an example in handler.py
docker run --env EARTHDATA_USERNAME --env EARTHDATA_PASSWORD cogify python -m handler 
```


Example Input:
```
{
    "collection": "OMDOAO3e",
    "href": "https://acdisc.gesdisc.eosdis.nasa.gov/data//Aura_OMI_Level3/OMDOAO3e.003/2022/OMI-Aura_L3-OMDOAO3e_2022m0120_v003-2022m0122t021759.he5",
    "upload": True,
    "granule_id":"G2205784904-GES_DISC"
}

```

Example Output
```
{
  "remote_fileurl": xxx,
  "filename": xxx,
  "granule_id": xxx,
  "collection": xxx,
}

```


## Other supported collections

### GPM IMERG Example

[Update me]

### ERA5 Cloud Base Height Example

ERA5 data is fetched using `cdsapi` library which first requires registration and API configuration, see https://cds.climate.copernicus.eu/api-how-to for instructions. 

Current configuration is for the cloud base height variable.

```bash
# First fetch the data
python3 ERA5/fetch.py
# Generate the cog
python3 run.py -f download.nc -c ERA5
```


AWS Provisioning:
To function as a lambda task, the Lambda function's execution role needs to be given permission to AWS PutObject.

- Add permission policy to the Lambda's execution role to allow `s3:PutObject`. This is because this Cogify lambda needs to access an S3 Bucket to write COG files
