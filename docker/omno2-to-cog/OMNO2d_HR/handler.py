from netCDF4 import Dataset
from affine import Affine
from rasterio.crs import CRS
from rasterio.io import MemoryFile
import re
from rio_cogeo.cogeo import cog_translate
from rio_cogeo.profiles import cog_profiles
import numpy as np
import argparse
import os
"""
This script converts an netCDF file stored on the local machine to COG.
It only accepts data which as the variables TroposphericNO2, LatitudeCenter and LongitudeCenter
(i.e. https://avdc.gsfc.nasa.gov/pub/data/satellite/Aura/OMI/V03/L3/OMNO2d_HR/OMNO2d_HRM/OMI_trno2_0.10x0.10_200410_Col3_V4.nc)
"""

parser = argparse.ArgumentParser(description="Generate COG from file and schema")
parser.add_argument("-f", "--filename", help="HDF5 or NetCDF filename to convert")
args = parser.parse_args()

# input file schema, for monthly data
f1 = dict(
    src_path=args.filename,
    variable_name="TroposphericNO2",
    lat_name="LatitudeCenter",
    lon_name="LongitudeCenter",
    nodata_value=9.969209968386869e+36,
    variable_transform=np.flipud
)

# For daily data
f2 = f1.copy()
f2['variable_name'] = 'NO2.COLUMN.VERTICAL.TROPOSPHERIC.CS30_BACKSCATTER.SOLAR'
f2['lat_name'] = 'LATITUDE'
f2['lon_name'] = 'LONGITUDE'
f2['nodata_value'] = -1.2676506e30

# Set COG inputs
output_profile = cog_profiles.get(
    "deflate"
)  # if the files aren't uint8, this will need to be changed
output_profile["blockxsize"] = 256
output_profile["blockysize"] = 256

def to_cog(
        src_path: str,
        variable_name: str,
        lat_name: str,
        lon_name: str,
        nodata_value: float,
        variable_transform: callable):
    """HDF/NetCDF to COG."""
    # Open existing dataset
    with Dataset(src_path, "r") as src:
        variable = src.variables[variable_name][:]
        lat = src.variables[lat_name][:]
        lon = src.variables[lon_name][:]
    # TODO throw error if given affine is the identity matrix
    # TODO consider case when lat lon give grid cell center
    # TODO investigate more flexible affine calculation
    # Manual calculation of affine
    xmin, ymin, xmax, ymax = [lon.min(), lat.min(), lon.max(), lat.max()]
    nrows, ncols = variable.shape[0], variable.shape[1]
    print("nrows, ncols: ", nrows, ncols)
    xres = (xmax - xmin) / float(ncols)
    yres = (ymax - ymin) / float(nrows)
    geotransform = (xmin, xres, 0, ymax, 0, -yres)
    dst_transform = Affine.from_gdal(*geotransform)

    # Save output as COG
    output_profile = dict(
        driver="GTiff",
        dtype=variable.dtype,
        count=1,
        height=nrows,
        width=ncols,
        crs=CRS.from_epsg(4326),
        transform=dst_transform,
        nodata=nodata_value,
        tiled=True,
        compress="deflate",
        blockxsize=256,
        blockysize=256,
    )
    print("profile h/w: ", output_profile["height"], output_profile["width"])
    with MemoryFile() as memfile:
        with memfile.open(**output_profile) as mem:
            mem.write(variable_transform(variable[:]), indexes=1)
        cog_translate(
            memfile,
            f"{os.path.splitext(src_path)[0]}.tif",
            output_profile,
            config=dict(GDAL_NUM_THREADS="ALL_CPUS", GDAL_TIFF_OVR_BLOCKSIZE="128"),
        )

day_regex = re.compile('\d{4}_\d{2}_\d{2}.+')
if day_regex.match(args.filename):
    to_cog(**f2)
else:
    to_cog(**f1)
