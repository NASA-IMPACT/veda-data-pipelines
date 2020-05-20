from pyhdf.SD import SD, SDC
from affine import Affine
import rasterio
from rasterio.crs import CRS
from rasterio.io import MemoryFile
from rio_cogeo.cogeo import cog_translate
from rio_cogeo.profiles import cog_profiles
from rasterio.warp import reproject, Resampling, calculate_default_transform
import numpy as np
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
variables = []
for var_name in f1["variable_names"]:
    variable = hdf.select(var_name)
    variables.append(variable[0])
    nodata_value = variable.getfillvalue()

# Get latitude / longitude bounds from metadata
metadata_strings = hdf.attributes()["ArchiveMetadata.0"].split("\n\n")
metadata_dict = dict()
for metadata_string in metadata_strings:
    if "OBJECT" in metadata_string:
        key_matches = re.search("OBJECT += (.+)$", metadata_string)
        value_matches = re.search("VALUE += (.+)\n", metadata_string)
        if key_matches and value_matches:
            metadata_dict[key_matches.group(1)] = value_matches.group(1)

xmin_bound, ymin_bound, xmax_bound, ymax_bound = [
    float(metadata_dict["WESTBOUNDINGCOORDINATE"]),
    float(metadata_dict["SOUTHBOUNDINGCOORDINATE"]),
    float(metadata_dict["EASTBOUNDINGCOORDINATE"]),
    float(metadata_dict["NORTHBOUNDINGCOORDINATE"]),
]
print("from bounding: ", xmin_bound, ymin_bound, xmax_bound, ymax_bound)

####
# Get latitude / longitude from XML
####
# Note: this seems problematic. At least in one case, one of the bounds
# was much different in the metadata from the `bounding coordinate` (e.g.
# longitudinal bounding coordinates were 179 + 172 but the minimum latitude in
# the XML metadata was -179.
# tree = ElementTree()
# xml = tree.parse(f"{f1['src_path']}.xml")
# print(xml)
# points = list(
#     xml.find(
#         "GranuleURMetaData/SpatialDomainContainer/HorizontalSpatialDomainContainer/GPolygon/Boundary"
#     )
# )
# lon = list(map(lambda p: float(p.find("PointLongitude").text), points))
# print("lons ", lon)
# lat = list(map(lambda p: float(p.find("PointLatitude").text), points))
# print("lats ", lat)
# xmin, ymin, xmax, ymax = [min(lon), min(lat), max(lon), max(lat)]
# print("from gring: ", xmin, ymin, xmax, ymax)
# Hard coding some things for now:
ulx = -160.016157073218
uly = 0.0150044604742833

# Review: Are we ever concerned that multiple variables will have different shapes?
nrows, ncols = variables[0].shape[0], variables[0].shape[1]
xres_g = (10) / float(ncols)
yres_g = (10) / float(nrows)
# geotransform = (xmin, xres, 0, ymax, 0, -yres)
# dst_transform = Affine.from_gdal(*geotransform)
# If you want to use Affine directly this is the same as `Affine.from_gdal()`:
src_transform = Affine(xres_g, 0, ulx, 0, -yres_g, uly)
print("transform from g_ring: ", src_transform)


###
# Save output as COG
###
# output_profile = dict(
#     driver="GTiff",
#     # TODO: Expand for greater than 2 variables
#     dtype=variables[0].dtype,
#     count=2,
#     height=nrows,
#     width=ncols,
#     crs=CRS.from_string(
#         "+proj=sinu +lon_0=0 +x_0=0 +y_0=0 +a=6371007.181 +b=6371007.181 +units=m +no_defs"
#     ),
#     transform=src_transform,
#     nodata=nodata_value,
#     tiled=True,
#     compress="deflate",
#     blockxsize=256,
#     blockysize=256,
# )

dst_transform = Affine(xres_g, 0, xmin_bound, 0, -yres_g, ymax_bound)
print("dst_transform: ", dst_transform)

# Calculating transform with rasterio
# src_crs = CRS.from_string(
#     "+proj=sinu +lon_0=0 +x_0=0 +y_0=0 +a=6371007.181 +b=6371007.181 +units=m +no_defs"
# )
# TODO should this be working?
# transform, width, height = calculate_default_transform(
#     src_crs,
#     CRS.from_epsg(4326),
#     ncols,
#     nrows,
#     xmin_bound,
#     ymin_bound,
#     xmax_bound,
#     ymax_bound,
# )
# print("rasterios default calc: ", transform, width, height)

# Reproject (this could be cleaned with a direct write, not two steps)
# output_var = np.zeros((nrows, ncols), np.float)

# reproject(
#     variables[0][:],
#     output_var,
#     src_transform=src_transform,
#     src_crs=src_profile["crs"],
#     dst_transform=dst_transform,
#     dst_crs=CRS.from_epsg(4326),
#     resampling=Resampling.nearest,
# )
# print("confirming data: ", output_var.max())
# print(variables[0][:].mean())

# with rasterio.open(
#     "/test_reproject.tif",
#     "w",
#     driver="GTiff",
#     height=output_var.shape[0],
#     width=output_var.shape[1],
#     count=1,
#     dtype=output_var.dtype,
#     crs=CRS.from_epsg(4326),
#     transform=dst_transform,
# ) as dst:
#     dst.write(output_var, indexes=1)

# print("profile h/w: ", output_profile["height"], output_profile["width"])
# with MemoryFile() as memfile:
#     with memfile.open(**output_profile) as mem:
#         # TODO: Expand for greater than 2 variables
#         mem.write(variables[0][:], indexes=1)
#         mem.write(variables[1][:], indexes=2)
#     cog_translate(
#         memfile,
#         f"{f1['src_path']}.tif",
#         output_profile,
#         config=dict(GDAL_NUM_THREADS="ALL_CPUS", GDAL_TIFF_OVR_BLOCKSIZE="128"),
#     )
