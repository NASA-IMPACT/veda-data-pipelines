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

output_bucket = 'cumulus-map-internal'
output_dir = 'cloud-optimized'

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

def rename(filename):
    """
    This is specific to GPM IMERG product
    """
    imerg_date = filename.split(".")[4].split('-')[0]
    replacement_date = f"{imerg_date[0:3]}_{imerg_date[4:5]}_{imerg_date[6:7]}"
    return f"{os.path.splitext(filename.replace(imerg_date, replacement_date))[0]}.tif"

def upload_file(outfilename, collection):
    return s3.upload_file(
        outfilename, output_bucket, f"{output_dir}/{collection}/{outfilename}"
    )

def to_cog(
        s3_path: str,
        group: str,
        variable_name: str):
    """HDF5 to COG."""
    # Open existing dataset
    src_filename = os.path.basename(s3_path)
    path_parts = s3_path.split('://')[1].split('/')
    bucket = path_parts[0]
    path = '/'.join(path_parts[1:])
    collection = path_parts[-2]
    s3.download_file(bucket, path, src_filename)
    src = Dataset(src_filename, "r")
    variable = src.groups[group][variable_name][:]
    xmin, ymin, xmax, ymax = [-180, -90, 180, 90]
    nrows, ncols = variable.shape[0], variable.shape[1]
    print("nrows, ncols: ", nrows, ncols)
    # TODO: Review - flipping IMERG
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
        # TODO: Review - flipping IMERG
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
            # TODO: Review - flipping IMERG
            mem.write(np.rot90(variable[:]), indexes=1) 
        outfilename = rename(src_filename)
        cog_translate(
            memfile,
            rename(src_filename),
            output_profile,
            config=dict(GDAL_NUM_THREADS="ALL_CPUS", GDAL_TIFF_OVR_BLOCKSIZE="128"),
        )
    upload_file(outfilename, collection)

to_cog(**f1)