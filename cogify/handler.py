from netCDF4 import Dataset
from affine import Affine
from rasterio.crs import CRS
from rasterio.io import MemoryFile
from rio_cogeo.cogeo import cog_translate
from rio_cogeo.profiles import cog_profiles
from rasterio.warp import calculate_default_transform
import numpy as np
import os
import requests
import boto3
from typing import Optional
import configparser
import argparse
import sys

config = configparser.ConfigParser()
config.read("example.ini")
s3 = boto3.client(
    "s3",
    aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
)

# Set COG inputs
output_profile = cog_profiles.get(
    "deflate"
)  # if the files aren't uint8, this will need to be changed
output_profile["blockxsize"] = 256
output_profile["blockysize"] = 256
output_bucket = config["DEFAULT"]["output_bucket"]
output_dir = config["DEFAULT"]["output_dir"]

parser = argparse.ArgumentParser(description="Cogify handler workflow")

parser.add_argument(
    "--collection",
    type=str,
    required=True,
    help="The name of the collection for the he5 data",
)

parser.add_argument(
    "--href", type=str, required=True, help="The href of he5 file to download"
)

parser.add_argument(
    "--upload", default=False, action="store_true", help="Upload cog to s3 bucket"
)
args = parser.parse_args()


def upload_file(outfilename, collection):
    filename = outfilename.split('/tmp/')[1]
    try:
        s3.upload_file(
            outfilename,
            output_bucket,
            f"{collection}/{filename}",
        )
        print('File uploaded to s3')
    except Exception as e:
        print("Failed to copy to S3 bucket")
        print(e)


def download_file(file_uri: str):
    filename = f"/tmp/{os.path.basename(file_uri)}"
    if "http" in file_uri:
        # This isn't working for GPMIMERG, need to use .netrc
        username = os.environ.get("EARTHDATA_USERNAME")
        password = os.environ.get("EARTHDATA_PASSWORD")
        with requests.Session() as session:
            session.auth = (username, password)
            request = session.request("get", file_uri)
            response = session.get(request.url, auth=(username, password))
            print("RESPONSE IS")
            print(response.status_code)
            with open(filename, "wb") as f:
                f.write(response.content)
    elif "s3://" in file_uri:
        path_parts = file_uri.split("://")[1].split("/")
        bucket = path_parts[0]
        path = "/".join(path_parts[1:])
        s3.download_file(bucket, path, filename)
    else:
        print(f"{filename} file already downloaded")
    return filename


def to_cog(**config):
    """HDF5 to COG."""
    # Open existing dataset
    filename = config["filename"]
    variable_name = config["variable_name"]
    x_variable, y_variable = config.get("x_variable"), config.get("y_variable")
    group = config.get("group")
    src = Dataset(filename, "r")

    if group is None:
        variable = src[variable_name][:]
        nodata_value = variable.fill_value
    else:
        variable = src.groups[group][variable_name]
        nodata_value = variable._FillValue
    # This may be just what we need for IMERG
    if config["collection"] == "GPM_3IMERGM":
        variable = np.transpose(variable[0])
    # This implies a global spatial extent, which is not always the case
    src_height, src_width = variable.shape[0], variable.shape[1]
    if x_variable and y_variable:
        xmin = src[x_variable][:].min()
        xmax = src[x_variable][:].max()
        ymin = src[y_variable][:].min()
        ymax = src[y_variable][:].max()
    else:
        xmin, ymin, xmax, ymax = [-180, -90, 180, 90]

    src_crs = config.get("src_crs")
    if src_crs:
        src_crs = CRS.from_proj4(src_crs)
    else:
        src_crs = CRS.from_epsg(4326)

    dst_crs = CRS.from_epsg(3857)

    # calculate dst transform
    dst_transform, dst_width, dst_height = calculate_default_transform(
        src_crs,
        dst_crs,
        src_width,
        src_height,
        left=xmin,
        bottom=ymin,
        right=xmax,
        top=ymax,
    )

    # https://github.com/NASA-IMPACT/cloud-optimized-data-pipelines/blob/rwegener2-envi-to-cog/docker/omno2-to-cog/OMNO2d.003/handler.py
    affine_transformation = config.get("affine_transformation")
    if affine_transformation:
        xres = (xmax - xmin) / float(src_width)
        yres = (ymax - ymin) / float(src_height)
        geotransform = eval(affine_transformation)
        dst_transform = Affine.from_gdal(*geotransform)

    # Save output as COG
    output_profile = dict(
        driver="GTiff",
        dtype=variable.dtype,
        count=1,
        crs=src_crs,
        transform=dst_transform,
        height=dst_height,
        width=dst_width,
        nodata=nodata_value,
        tiled=True,
        compress="deflate",
        blockxsize=256,
        blockysize=256,
    )
    print("profile h/w: ", output_profile["height"], output_profile["width"])
    outfilename = f"{filename}.tif"
    with MemoryFile() as memfile:
        with memfile.open(**output_profile) as mem:
            data = variable.astype(np.float32)
            mem.write(data, indexes=1)
        cog_translate(
            memfile,
            outfilename,
            output_profile,
            config=dict(GDAL_NUM_THREADS="ALL_CPUS", GDAL_TIFF_OVR_BLOCKSIZE="128"),
        )
    return outfilename


def handler(event, context):
    filename = event["href"]
    collection = event["collection"]
    to_cog_config = config._sections[collection]
    downloaded_filename = download_file(file_uri=filename)
    to_cog_config["filename"] = downloaded_filename
    to_cog_config["collection"] = collection
    outfilename = to_cog(**to_cog_config)

if __name__ == "__main__":
    sample_event = {"collection": args.collection, "href": args.href}
    handler(sample_event, {})
