from netCDF4 import Dataset
from affine import Affine
from rasterio.crs import CRS
from rasterio.io import MemoryFile
from rio_cogeo.cogeo import cog_translate
from rio_cogeo.profiles import cog_profiles
import numpy as np
import argparse
import os
import boto3

parser = argparse.ArgumentParser(description="Generate COG from file and schema")
parser.add_argument("-f", "--filename", help="HDF5 or NetCDF filename to convert")
args = parser.parse_args()
s3 = boto3.client('s3')

# input file schema
f1 = dict(
    s3_path=args.filename,
    group="Grid",
    variable_name="precipitationCal"
)

# Set COG inputs
output_profile = cog_profiles.get(
    "deflate"
)  # if the files aren't uint8, this will need to be changed
output_profile["blockxsize"] = 256
output_profile["blockysize"] = 256

def to_cog(
        s3_path: str,
        group: str,
        variable_name: str):
    """HDF5 to COG."""
    # Open existing dataset
    src_path = os.path.basename(s3_path)
    bucket = s3_path.split('://')[1].split('/')[0]
    path = '/'.join(s3_path.split('://')[1].split('/')[1:])
    s3.download_file(bucket, path, src_path)
    src = Dataset(src_path, "r")
    variable = src.groups[group][variable_name][:]
    xmin, ymin, xmax, ymax = [-180, -90, 180, 90]
    nrows, ncols = variable.shape[0], variable.shape[1]
    print("nrows, ncols: ", nrows, ncols)
    xres = (xmax - xmin) / float(nrows)
    yres = (ymax - ymin) / float(ncols)
    geotransform = (xmin, xres, 0, ymax, 0, yres)
    dst_transform = Affine.from_gdal(*geotransform)
    nodata_value = variable.fill_value

    # Save output as COG
    output_profile = dict(
        driver="GTiff",
        dtype=variable.dtype,
        count=1,
        # not sure this is correct, we need to flip things around
        height=ncols,
        width=nrows,
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
            # TODO: Review if necessary
            mem.write(np.rot90(variable[:]), indexes=1)        
        cog_translate(
            memfile,
            f"{os.path.splitext(src_path)[0]}.tif",
            output_profile,
            config=dict(GDAL_NUM_THREADS="ALL_CPUS", GDAL_TIFF_OVR_BLOCKSIZE="128"),
        )

to_cog(**f1)