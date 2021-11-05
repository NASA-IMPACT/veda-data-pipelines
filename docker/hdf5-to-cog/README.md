# NetCDF4 / HDF5 to COG

🚧 WIP 🚧 Configurable module for converting NetCDF4 / HDF5 to COG.

At this time, just 2 configurations have been made in `example.ini`.

Before running the commands below, make sure you `cd docker/hdf5-to-cog`.

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
export USERNAME=aimeeb
export PASSWORD=xxx
unset GDAL_DATA
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
# Test it
python3 run.py \
  -c OMINO2 \
  -f ../../sample-files/OMI-Aura_L3-OMNO2d_2004m1001_v003-2019m1121t082956.he5
```