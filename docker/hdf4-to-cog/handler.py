from pyhdf.SD import SD, SDC
from affine import Affine
import rasterio
from rasterio.crs import CRS
from rasterio.io import MemoryFile
from rio_cogeo.cogeo import cog_translate
from rio_cogeo.profiles import cog_profiles
from rasterio.warp import reproject, Resampling, calculate_default_transform
import numpy as np
from ast import literal_eval
import argparse
from xml.etree.ElementTree import ElementTree
import re, os

"""
This script converts an netCDF file stored on the local machine to COG.
It only accepts data which as the variables TroposphericNO2, LatitudeCenter and LongitudeCenter
(i.e. https://avdc.gsfc.nasa.gov/pub/data/satellite/Aura/OMI/V03/L3/OMNO2d_HR/OMNO2d_HRM/OMI_trno2_0.10x0.10_200410_Col3_V4.nc)
"""

parser = argparse.ArgumentParser(description="Generate COG from file and schema")
parser.add_argument("-f", "--filename", help="HDF5 or NetCDF filename to convert")
parser.add_argument(
    "--cog", action="store_true", help="Output should be a cloud-optimized geotiff"
)
args = parser.parse_args()

# input file schema
f1 = dict(
    src_path=args.filename, variable_names=["Optical_Depth_047", "Optical_Depth_055"]
)

hdf = SD(f1["src_path"], SDC.READ)
# TODO dataset tags
# print("hdf attribute keys: ", hdf.attributes().keys())
## ['HDFEOSVersion', 'StructMetadata.0', 'Orbit_amount', 'Orbit_time_stamp',
# 'CoreMetadata.0', 'ArchiveMetadata.0', 'identifier_product_doi',
# 'identifier_product_doi_authority']
# print(hdf.attributes()["identifier_product_doi"])  # 10.5067/MODIS/MCD19A2.006

variables = [hdf.select(var_name) for var_name in f1["variable_names"]]

# Get projected coord polygon from metadata for src_tranform
metadata_strings = hdf.attributes()["StructMetadata.0"].rstrip("\x00").split("\n")
metadata_dict = dict()
for metadata_string in metadata_strings:
    # TODO remove redundant code
    if "UpperLeftPointMtrs" in metadata_string:
        key = metadata_string.split("=")[0]
        key = re.sub("\t", "", key)
        value = metadata_string.split("=")[1]
        metadata_dict[key] = literal_eval(value)
    if "LowerRightMtrs" in metadata_string:
        key = metadata_string.split("=")[0]
        key = re.sub("\t", "", key)
        value = metadata_string.split("=")[1]
        metadata_dict[key] = literal_eval(value)

# Construct src affine transform
minx, maxy, maxx, miny = [
    metadata_dict["UpperLeftPointMtrs"][0],
    metadata_dict["UpperLeftPointMtrs"][1],
    metadata_dict["LowerRightMtrs"][0],
    metadata_dict["LowerRightMtrs"][1],
]

# TODO: This is problematic for 2 reasons:
# 1. It is possible different variables have different dimensions
# 2. Dimensions actually start at index 0, here we have dims 1 and 2 which is
# specific to the AOD data set which has a first dimension we are ignoring
# 'Orbits:grid1km'
# REVIEW: Should we be ignoring this dimension? we may want to include each
# orbit as a new band?
src_width, src_height = variables[0].dim(1).length(), variables[0].dim(2).length()
xres_g = (maxx - minx) / float(src_width)
yres_g = (maxy - miny) / float(src_height)
src_transform = Affine(xres_g, 0, minx, 0, -yres_g, maxy)

# Define src and dst CRS
src_crs = CRS.from_string(
    "+proj=sinu +lon_0=0 +x_0=0 +y_0=0 +ellps=WGS84 +R=6371007.181 +datum=WGS84 +units=m +no_defs"
)
dst_crs = "EPSG:4326"

# calculate dst transform
dst_transform, dst_width, dst_height = calculate_default_transform(
    src_crs, dst_crs, src_width, src_height, minx, miny, maxx, maxy
)

# TODO: Expand dtype and nodata value for greater than 2 variables
# dtypes = tuple(var[0].dtype for var in variables)
# nodata_values = tuple(var.getfillvalue() for var in variables)

# Define profile values for final tif
# Assumption: nodata value is the same for all bands
scale_factor = variables[0].attributes()["scale_factor"]
output_profile = dict(
    driver="GTiff",
    dtype=np.float32,
    count=2,
    height=dst_height,
    width=dst_width,
    crs=dst_crs,
    transform=dst_transform,
    nodata=np.float32(variables[0].getfillvalue()) * scale_factor,
    tiled=True,
    compress="deflate",
    blockxsize=256,
    blockysize=256,
)

# Reproject, tile, and save
with MemoryFile() as memfile:
    with memfile.open(**output_profile) as mem:
        for idx, data_var in enumerate(variables):
            print(f"idx is {idx}")
            mem.set_band_description(idx + 1, f1["variable_names"][idx])
            # TODO appropriate tags
            reproject(
                source=data_var[0][:].astype(np.float32) * scale_factor,
                destination=rasterio.band(mem, idx + 1),
                src_transform=src_transform,
                src_crs=src_crs,
                dst_transform=mem.transform,
                dst_crs=mem.crs,
                resampling=Resampling.nearest,
            )

    output_filename = f"{os.path.splitext(f1['src_path'])[0]}.tif"
    if args.cog == False:
        with rasterio.open(output_filename, "w", **output_profile) as dst:
            dst.write(memfile.open().read())
            dst.close()
    else:
        cog_translate(
            memfile,
            output_filename.replace(".tif", "_cog.tif"),
            output_profile,
            config=dict(GDAL_NUM_THREADS="ALL_CPUS", GDAL_TIFF_OVR_BLOCKSIZE="128"),
        )
