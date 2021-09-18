from netCDF4 import Dataset
from affine import Affine
from rasterio.crs import CRS
from rasterio.io import MemoryFile
from rio_cogeo.cogeo import cog_translate
from rio_cogeo.profiles import cog_profiles
from rasterio.warp import calculate_default_transform
import numpy as np
import argparse
import os
import requests
import boto3
from typing import Optional
import configparser
config = configparser.ConfigParser()
config.read('example.ini')

parser = argparse.ArgumentParser(description="Generate COG from file and schema")
parser.add_argument("-f", "--filename", help="HDF5 or NetCDF filename to convert")
parser.add_argument('-c', '--collection', help='Collection config to use in conversion')
args = parser.parse_args()
s3 = boto3.client('s3')

# Set COG inputs
output_profile = cog_profiles.get(
    "deflate"
)  # if the files aren't uint8, this will need to be changed
output_profile["blockxsize"] = 256
output_profile["blockysize"] = 256
output_bucket = config['DEFAULT']['output_bucket']
output_dir = config['DEFAULT']['output_dir']

def upload_file(outfilename, collection):
    return s3.upload_file(
        outfilename, output_bucket, f"{output_dir}/{collection}/{outfilename}",
        ExtraArgs={'ACL': 'public-read'}
    )

def download_file(file_uri: str):
    filename = os.path.basename(file_uri)
    print(filename)
    if 'http' in file_uri:
        # This isn't working for GPMIMERG, need to use .netrc
        username = os.environ.get('USERNAME')
        password = os.environ.get('PASSWORD')
        session = requests.Session()
        session.auth = (username, password)
        response = session.get(file_uri)
        with open(filename, 'wb') as f:
            f.write(response.content)
    elif 's3://' in file_uri:
        path_parts = file_uri.split('://')[1].split('/')
        bucket = path_parts[0]
        path = '/'.join(path_parts[1:])
        s3.download_file(bucket, path, filename) 
    else:
        print(f"{filename} file already downloaded")
    return filename

def to_cog(
        filename: str,
        variable_name: str,
        group: Optional[str] = None):
    """HDF5 to COG."""
    # Open existing dataset
    # filename = 'L2GCOV_NASADEM_UTM-lopenp_14043_16008_009_160225_L090_CX_02.h5'
    # f = h5py.File(filename, 'r')
    src = Dataset(filename, "r")
    if group is None:
        # netcdf4
        variable = src[variable_name][:]
        nodata_value = variable.fill_value
    else:
        # hdf5
        # NISAR HDF5 
        # variable = src.groups['science'].groups['LSAR'].groups['GCOV'].groups['grids'].groups['frequencyA']['HVHV']
        # gdalinfo HDF5:"L2GCOV_NASADEM_UTM-lopenp_14043_16008_009_160225_L090_CX_02.h5"://science/LSAR/GCOV/grids/frequencyA/HHHH -stats
        variable = src.groups[group][variable_name]
        nodata_value = variable._FillValue
    # np.transpose required for GPMIMERG data
    # TODO: Send variable to collection-specifc "process" function
    # Import collection-specific modules for variable "process" (and in the future for "fetch")
    # import GPMIMERG
    # variable = GPMIMERG.process(variable) --> variable = np.transpose(variable[0])
    src_height, src_width = variable.shape[0], variable.shape[1]
    xmin, ymin, xmax, ymax = [-180, -90, 180, 90]
    xres = (xmax - xmin) / float(src_height)
    yres = (ymax - ymin) / float(src_width)
    src_crs = CRS.from_epsg(4326)
    dst_crs = CRS.from_epsg(4326)

    # calculate dst transform
dst_transform, dst_width, dst_height = calculate_default_transform(
    src_crs, dst_crs, src_width, src_height, xmin, ymin, xmax, ymax
)
    # Save output as COG
output_profile = dict(
    driver="GTiff",
    dtype=variable.dtype,
    count=1,
    crs=src_crs,
    transform=dst_transform,
    height=dst_height,
    width=dst_width,
    #nodata=nodata_value,
    tiled=True,
    compress="deflate",
    blockxsize=256,
    blockysize=256,
)
    print("profile h/w: ", output_profile["height"], output_profile["width"])
outfilename = f'{filename}.tif'
with MemoryFile() as memfile:
    with memfile.open(**output_profile) as mem:
        data = variable.astype(np.float32)
        mem.write(data)
    cog_translate(
        memfile,
        outfilename,
        output_profile,
        config=dict(GDAL_NUM_THREADS="ALL_CPUS", GDAL_TIFF_OVR_BLOCKSIZE="128"),
    )
        return outfilename

filename = args.filename
collection = args.collection
downloaded_filename = download_file(file_uri=filename)
to_cog_config = config._sections[collection]
to_cog_config['filename'] = downloaded_filename
outfilename = to_cog(**to_cog_config)
print(outfilename)
