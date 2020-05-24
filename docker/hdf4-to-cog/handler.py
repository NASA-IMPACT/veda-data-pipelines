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
import re, os
import collection_helpers

"""
This script converts an HDF4 file stored on the local machine to COG.
"""

parser = argparse.ArgumentParser(description="Generate COG from file and schema")
parser.add_argument("-f", "--filename", help="MODIS HDF4 filename to convert")
parser.add_argument(
    "--cog", action="store_true", help="Output should be a cloud-optimized geotiff"
)
parser.add_argument(
    "-c", "--collection",
    help="Indicates the input file is associated with this MODIS collection. " +
         "AOD and VI supported. Used in configuring COG conversion."
)
parser.add_argument(
    "-d", "--directory",
    help="Directory where file is stored",
    default=""
)
args = parser.parse_args()

# input schemas
modis_config = dict(
    src_crs="+proj=sinu +lon_0=0 +x_0=0 +y_0=0 +ellps=WGS84 +R=6371007.181 +datum=WGS84 +units=m +no_defs"
)

modis_aod_config = dict(
    variable_names=["Optical_Depth_047", "Optical_Depth_055"],
    twod_band_dims = [1,2],
    src_crs=modis_config['src_crs'],
    dimension_select_function='select_from_orbits',
    selection_args = dict(orbit_sds_name='cosVZA')
)

modis_vi_config = dict(
    variable_names=["250m 16 days NDVI", "250m 16 days EVI"],
    twod_band_dims = [0,1],
    src_crs=modis_config['src_crs']
)

modis_vi_monthly_config = modis_vi_config.copy()
modis_vi_monthly_config['variable_names'] = ["1 km monthly NDVI", "1 km monthly EVI"]
modis_vi_500m_config = modis_vi_config.copy()
modis_vi_500m_config['variable_names'] = ["500m 16 days NDVI", "500m 16 days EVI"]

collection_configs = dict(
    AOD=modis_aod_config,
    VI=modis_vi_config,
    VI_MONTHLY=modis_vi_monthly_config,
    VI_500M=modis_vi_500km_config
)

config = collection_configs[args.collection]
print(f"Starting on {args.directory}{args.filename}")
hdf = SD(f"{args.directory}{args.filename}", SDC.READ)

variables = [hdf.select(var_name) for var_name in config["variable_names"]]

# Get projected coord polygon from metadata for src_tranform
metadata_strings = hdf.attributes()["StructMetadata.0"].rstrip("\x00").split("\n")
metadata_dict = dict()

for metadata_string in metadata_strings:
    if "UpperLeftPointMtrs" in metadata_string or "LowerRightMtrs" in metadata_string:
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

src_width = variables[0].dim(config['twod_band_dims'][0]).length()
src_height = variables[0].dim(config['twod_band_dims'][1]).length()
xres_g = (maxx - minx) / float(src_width)
yres_g = (maxy - miny) / float(src_height)
src_transform = Affine(xres_g, 0, minx, 0, -yres_g, maxy)

# Define src and dst CRS
src_crs = CRS.from_string(config['src_crs'])
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
    count=len(variables),
    height=dst_height,
    width=dst_width,
    crs=dst_crs,
    transform=dst_transform,
    nodata=variables[0].getfillvalue(),
    tiled=True,
    compress="deflate",
    blockxsize=256,
    blockysize=256,
)

# Reproject, tile, and save
with MemoryFile() as memfile:
    with memfile.open(**output_profile) as mem:
        for idx, data_var in enumerate(variables):
            mem.set_band_description(idx + 1, config["variable_names"][idx])
            if config.get('dimension_select_function'):
                function_to_call = getattr(collection_helpers, config['dimension_select_function'])
                band_data = function_to_call(config['selection_args'], hdf, data_var)
            else:
                band_data = data_var[:]
            reproject(
                # Choose which orbit to put in the band
                source=band_data,
                destination=rasterio.band(mem, idx + 1),
                src_transform=src_transform,
                src_crs=src_crs,
                dst_transform=mem.transform,
                dst_crs=mem.crs,
                resampling=Resampling.nearest,
            )

    output_filename = f"{args.directory}{os.path.splitext(args.filename)[0]}.tif"
    print(f"Generating tif {output_filename}")
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
