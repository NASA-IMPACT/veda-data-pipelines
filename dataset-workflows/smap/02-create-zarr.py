import os
import re
import datetime

import xarray as xr

from dask.distributed import Client
client = Client() 

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
    fname = os.path.basename(d_am_raw.encoding["source"])
    fdate_str = re.search(r'(?<=_SM_P_)\d+(?=_)', fname).group()
    fdate = datetime.datetime.strptime(fdate_str, "%Y%m%d")
    dim_names = sorted(d_am_raw.dims.keys())
    is_am = dim_names[0] == "phony_dim_0"
    d_am = d_am_raw
    d_am = d_am.rename_dims({
        dim_names[0]: "easting_m",
        dim_names[1]: "northing_m",
        dim_names[2]: "ranked_land_cover"
    })
    # NOTE: Upper-left to lower-right; therefore, x increases but y decreases
    d_am = d_am.assign_coords({
        "easting_m": ulx + x_size * d_am.easting_m,
        "northing_m": uly - y_size * d_am.northing_m,
        "datetime": fdate
    })
    d_am = d_am.expand_dims('datetime', axis=2)
    use_vars = ["albedo",
                "bulk_density",
                "clay_fraction",
                "freeze_thaw_fraction",
                "grid_surface_status",
                "radar_water_body_fraction",
                "retrieval_qual_flag",
                "roughness_coefficient",
                "soil_moisture",
                "soil_moisture_error",
                "static_water_body_fraction",
                "surface_flag",
                "surface_temperature"]
    if not is_am:
        use_vars = [v + "_pm" for v in use_vars]
    return d_am[use_vars]

print("Reading files...")
dat_am = xr.open_mfdataset(datafiles,
                           preprocess=mypreproc,
                           combine='by_coords',
                           group="Soil_Moisture_Retrieval_Data_AM")

dat_pm = xr.open_mfdataset(datafiles,
                           preprocess=mypreproc,
                           combine='by_coords',
                           group="Soil_Moisture_Retrieval_Data_PM")

print("Altering chunking strategy...")
dat_both = xr.merge((dat_am, dat_pm)).chunk({"easting_m": 50, "northing_m": 50, "datetime": 50})
print("Writing Zarr output...")
zarr_path = short_name + ".zarr"
dat_both.to_zarr(zarr_path, consolidated=True, mode='w')
print("Done!")
