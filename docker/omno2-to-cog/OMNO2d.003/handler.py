from netCDF4 import Dataset
from affine import Affine
from rasterio.crs import CRS
from rasterio.io import MemoryFile
from rio_cogeo.cogeo import cog_translate
from rio_cogeo.profiles import cog_profiles
from ast import literal_eval
import numpy as np
import argparse
import h5py
import os

"""
This script converts an netCDF file stored on the local machine to COG.
Grab data from: https://acdisc.gesdisc.eosdis.nasa.gov/data/Aura_OMI_Level3/OMNO2d.003/
"""

parser = argparse.ArgumentParser(description="Generate COG from file and schema")
parser.add_argument("-f", "--filename", help="HDF5 or NetCDF filename to convert")
args = parser.parse_args()

# input file schema
f1 = dict(
    src_path=args.filename,
    variable_name="//HDFEOS/GRIDS/ColumnAmountNO2/Data_Fields/ColumnAmountNO2TropCloudScreened",
    lat_name="LatitudeCenter",
    lon_name="LongitudeCenter",
    nodata_value=-1.2676506e30,
    variable_transform=np.flipud,
)

# Set COG inputs
output_profile = cog_profiles.get(
    "deflate"
)  # if the files aren't uint8, this will need to be changed
output_profile["blockxsize"] = 256
output_profile["blockysize"] = 256


def extract_tags(attributes):
    """Create dict of tags from HDF attributes object"""
    tags = {}
    for key, value in attributes.items():
        # Sanitize
        if value.__class__ is np.bytes_:
            value = value.decode("utf-8")
        if value.__class__ is np.ndarray and len(value) == 1:
            value = value[0]
        if key == "MissingValue" or key == "_FillValue":
            continue
        # Add to final dict
        tags[key] = value
    return tags


def to_cog(
    src_path: str,
    variable_name: str,
    lat_name: str,
    lon_name: str,
    nodata_value: float,
    variable_transform: callable,
):
    """HDF/NetCDF to COG."""
    with h5py.File(src_path, "r") as src:
        no2_attrs = src["HDFEOS"]["GRIDS"]["ColumnAmountNO2"].attrs
        xmin, xmax, ymin, ymax = literal_eval(no2_attrs["GridSpan"].decode("utf-8"))
        variable = src["HDFEOS"]["GRIDS"]["ColumnAmountNO2"]["Data Fields"][
            "ColumnAmountNO2TropCloudScreened"
        ][:]
        # Persist metadata
        file_tags = extract_tags(src["HDFEOS"]["ADDITIONAL"]["FILE_ATTRIBUTES"].attrs)
        dataset_tags = extract_tags(
            src["HDFEOS"]["GRIDS"]["ColumnAmountNO2"]["Data Fields"][
                "ColumnAmountNO2TropCloudScreened"
            ].attrs
        )

    # Manual calculation of affine
    nrows, ncols = variable.shape[0], variable.shape[1]
    xres = (xmax - xmin) / float(ncols)
    yres = (ymax - ymin) / float(nrows)
    geotransform = (xmin, xres, 0, ymax, 0, -yres)
    dst_transform = Affine.from_gdal(*geotransform)

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

    with MemoryFile() as memfile:
        with memfile.open(**output_profile) as mem:
            mem.write(variable_transform(variable[:]), indexes=1)
            mem.update_tags(**dataset_tags)
            mem.update_tags(**file_tags)
            mem.set_band_description(1, "ColumnAmountNO2TropCloudScreened")
        cog_translate(
            memfile,
            f"{os.path.splitext(src_path)[0]}.tif",
            output_profile,
            config=dict(GDAL_NUM_THREADS="ALL_CPUS", GDAL_TIFF_OVR_BLOCKSIZE="128"),
        )


to_cog(**f1)
