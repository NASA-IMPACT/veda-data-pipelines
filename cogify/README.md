# NetCDF4 / HDF5 to COG

🚧 WIP 🚧 Configurable module for converting NetCDF4 / HDF5 to COG.

At this time, just 2 configurations have been made in `example.ini`.

Before running the commands below, make sure you `cd docker/`.

## With docker

```bash
export EARTHDATA_USERNAME=xxx
export EARTHDATA_PASSWORD=XXX

docker build --build-arg EARTHDATA_USERNAME --build-arg EARTHDATA_PASSWORD -t cogify .
```

## GPM IMERG Example

GPM IMERG data is fetched over HTTP using `.netrc` for URS credentials. Current configuration is for the preciptation variable.

Add to your `~/.netrc` file

```bash
machine urs.earthdata.nasa.gov
	login aimeeb
	password XXX
```

Run the transofrm

```bash
# Test it
unset GDAL_DATA
DOWNLOAD=true
pyenv exec python run.py \
  -c GPM_3IMERGM \
  -f https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGM.06/2020/3B-MO.MS.MRG.3IMERG.20200501-S000000-E235959.05.V06B.HDF5
```

## ERA5 Cloud Base Height Example

ERA5 data is fetched using `cdsapi` library which first requires registration and API configuration, see https://cds.climate.copernicus.eu/api-how-to for instructions. 

Current configuration is for the cloud base height variable.

```bash
# First fetch the data
python3 ERA5/fetch.py
# Generate the cog
python3 run.py -f download.nc -c ERA5
```

## OMI NO2 Example

```bash
# needs environment variables
docker build -t cogify .
export EARTHDATA_USERNAME=xxx
export EARTHDATA_PASSWORD=xxx
docker run --env EARTHDATA_USERNAME --env EARTHDATA_PASSWORD cogify python -m handler --collection xxx --filename xxx
```
