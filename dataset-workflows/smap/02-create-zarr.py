import os
import re
import datetime
import shutil

import xarray as xr

from dask.distributed import Client
client = Client() 

import faulthandler
faulthandler.enable()

short_name = "SPL3SMP"
datafiles_all = sorted(os.listdir(short_name))
datafiles = [short_name + '/' + f for f in datafiles_all if f.endswith("h5")]

# EASE grid information
ncols = 964
nrows = 406
x_size = 36032.22  # meters
y_size = 36032.22  # meters
ulx = -17367530.45
uly = 7314540.83
ease_epsg = "epsg:6933"

# Preprocessing function -- takes dataset as an argument
def mypreproc(d_am_raw):
    # df = xr.open_dataset(datafiles[0], engine="h5netcdf")
    # d_am_raw = xr.open_dataset(df, "Soil_Moisture_Retrieval_Data_AM")
    fname = os.path.basename(d_am_raw.encoding["source"])
    fdate_str = re.search(r'(?<=_SM_P_)\d+(?=_)', fname).group()
    fdate = datetime.datetime.strptime(fdate_str, "%Y%m%d")
    d_am = d_am_raw
    d_am = d_am.rename_dims({
        "phony_dim_0": "easting_m",
        "phony_dim_1": "northing_m",
        "phony_dim_2": "ranked_land_cover"
    })
    # NOTE: Upper-left to lower-right; therefore, x increases but y decreases
    d_am = d_am.assign_coords({
        "easting_m": ulx + x_size * d_am.easting_m,
        "northing_m": uly - y_size * d_am.northing_m,
        "datetime": fdate
    }).drop_vars(["EASE_column_index",
                  "EASE_row_index"])
    d_am = d_am.expand_dims('datetime', axis=2)
    return d_am

print("Reading files...")
dat_am = xr.open_mfdataset(datafiles,
                           preprocess=mypreproc,
                           combine='by_coords',
                           group="Soil_Moisture_Retrieval_Data_AM")

print("Creating un-chunked Zarr array...")
dat_am.to_zarr(f'{short_name}-raw.zarr', consolidated=True, mode='w')

print("Altering chunking strategy...")
dat_am_2 = dat_am.chunk({"easting_m": 50, "northing_m": 50, "datetime": 50})
zarr_path = short_name + ".zarr"
print("Removing existing Zarr directory (if present)...")
shutil.rmtree(zarr_path, ignore_errors=True)
print("Writing Zarr output...")
dat_am_2.to_zarr(zarr_path, consolidated=True)
print("Done!")
