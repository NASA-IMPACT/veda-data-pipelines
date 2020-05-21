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

variables = []
for var_name in f1["variable_names"]:
    variable = hdf.select(var_name)
    variables.append(variable[0])
    nodata_value = variable.getfillvalue()

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

src_width, src_height = variables[0].shape[1], variables[0].shape[0]
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

# Define profile values for final tif
output_profile = dict(
    driver="GTiff",
    # TODO: Expand for greater than 2 variables
    dtype=variables[0].dtype,
    count=1,
    height=dst_height,
    width=dst_width,
    crs=dst_crs,
    transform=dst_transform,
    nodata=nodata_value,
    tiled=True,
    compress="deflate",
    blockxsize=256,
    blockysize=256,
)
print("src: ", src_transform)
print(src_width, src_height)
print("dst: ", dst_transform)
print(dst_width, dst_height)

# Reproject, tile, and save
with MemoryFile() as memfile:
    with memfile.open(**output_profile) as mem:
        # TODO: Expand for greater than 2 variables
        mem.set_band_description(1, "Optical_Depth_047")
        # TODO appropriate tags
        reproject(
            source=variables[0][:],
            destination=rasterio.band(mem, 1),
            src_transform=src_transform,
            src_crs=src_crs,
            dst_transform=mem.transform,
            dst_crs=mem.crs,
            resampling=Resampling.nearest,
        )
        # TODO write out second variable

    cog_translate(
        memfile,
        f"{os.path.splitext(f1['src_path'])[0]}.tif",
        output_profile,
        config=dict(GDAL_NUM_THREADS="ALL_CPUS", GDAL_TIFF_OVR_BLOCKSIZE="128"),
    )
