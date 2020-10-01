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
import requests
from tinynetrc import Netrc
from helpers import rename_imerg

parser = argparse.ArgumentParser(description="Generate COG from file and schema")
parser.add_argument("-f", "--filename", help="HDF5 or NetCDF filename to convert")
parser.add_argument('-c', '--collection', help='Collection name')
args = parser.parse_args()
s3 = boto3.client('s3')
ssm = boto3.client('ssm', region_name="us-east-1")

output_bucket = 'cumulus-map-internal'
output_dir = 'cloud-optimized'

# input file schema
# for daily netcdf data
collection_configs = {
    # Monthly HDF5
    'GPM_3IMERGM': dict(
        group="Grid",
        variable_name="precipitation",
        monthly=True,
        rename_file=rename_imerg),
    # Daily NetCDF4
    'GPM_3IMERGF': dict(
        variable_name="precipitationCal",
        rename_file=rename_imerg)
}

# Set COG inputs
output_profile = cog_profiles.get(
    "deflate"
)  # if the files aren't uint8, this will need to be changed
output_profile["blockxsize"] = 256
output_profile["blockysize"] = 256

def upload_file(outfilename, collection):
    return s3.upload_file(
        outfilename, output_bucket, f"{output_dir}/{collection}/{outfilename}",
        ExtraArgs={'ACL': 'public-read'}
    )

def download_file(file_uri: str):
    filename = os.path.basename(file_uri)
    print(filename)
    print(file_uri)
    if 'http' in file_uri:
        # download file using username password
        open('/root/.netrc', 'w').close()
        netrc = Netrc()
        ssm_prefix = os.environ.get("SSM_PREFIX")
        username_parameter = ssm.get_parameter(Name=f"/{ssm_prefix}/EARTHDATA_USERNAME", WithDecryption=True)
        password_parameter = ssm.get_parameter(Name=f"/{ssm_prefix}/EARTHDATA_PASSWORD", WithDecryption=True)
        netrc['urs.earthdata.nasa.gov']['login'] = username_parameter['Parameter']['Value']
        netrc['urs.earthdata.nasa.gov']['password'] = password_parameter['Parameter']['Value']
        netrc.save()
        response = requests.get(file_uri)
        with open(filename, 'wb') as f:
            f.write(response.content)
    elif 's3://' in file_uri:
        path_parts = file_uri.split('://')[1].split('/')
        bucket = path_parts[0]
        path = '/'.join(path_parts[1:])
        s3.download_file(bucket, path, filename)
    return dict(filename=filename)

def to_cog(
        filename: str,
        group: str,
        monthly: bool,
        variable_name: str,
        rename_file: callable):
    """HDF5 to COG."""
    # Open existing dataset
    src = Dataset(filename, "r")
    if group is None:
        variable = src[variable_name][:]
    else:
        variable = src.groups[group][variable_name][:]
    xmin, ymin, xmax, ymax = [-180, -90, 180, 90]
    nrows, ncols = variable.shape[1], variable.shape[2]
    print("nrows, ncols: ", nrows, ncols)
    # TODO: Review - flipping IMERG
    xres = (xmax - xmin) / float(nrows)
    yres = (ymax - ymin) / float(ncols)
    geotransform = (xmin, xres, 0, ymax, 0, -yres)
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
            mem.write(np.rot90(variable[:][0].data), indexes=1)
        outfilename = rename_file(filename, monthly)
        cog_translate(
            memfile,
            outfilename,
            output_profile,
            config=dict(GDAL_NUM_THREADS="ALL_CPUS", GDAL_TIFF_OVR_BLOCKSIZE="128"),
        )
        return outfilename

filename = args.filename
collection = args.collection
if os.environ.get('ENV') != 'test':
    file_args = download_file(file_uri=filename)
    filename = file_args['filename']

config = collection_configs.get(collection)
config['filename'] = filename
outfilename = to_cog(**config)

if os.environ.get('ENV') != 'test':
    upload_file(outfilename, collection)

