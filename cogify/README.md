# NetCDF4 / HDF5 to COG

🚧 WIP 🚧 Configurable module for converting NetCDF4 / HDF5 to COG.

At this time, just a few configurations have been made in `example.ini`.

Before running the commands below, make sure you `cd cogify/`.

## Testing

`handler.py` by default is using an example with OMI NO2 data.

```bash
export EARTHDATA_USERNAME=xxx
export EARTHDATA_PASSWORD=XXX

docker build -t cogify .
# Runs an example in handler.py
docker run --env EARTHDATA_USERNAME --env EARTHDATA_PASSWORD cogify handler
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
