from rasterio.crs import CRS
from rasterio.io import MemoryFile
from rio_cogeo.cogeo import cog_translate
from rio_cogeo.profiles import cog_profiles
import rasterio
import numpy as np
import argparse
import os

parser = argparse.ArgumentParser(description="Generate COG from .img file and schema")
parser.add_argument("-f", "--filename", help="filename to convert")
args = parser.parse_args()

# input file schema
f1 = dict(
    src_path=args.filename
)

# Set COG inputs
output_profile = cog_profiles.get(
    "deflate"
)  # if the files aren't uint8, this will need to be changed
output_profile["blockxsize"] = 256
output_profile["blockysize"] = 256


def to_cog(
    src_path: str
):
    with rasterio.open(src_path) as src:
        print(src.meta)
        variable = src.read(3)
        transform = src.transform
        nodata_value = src.nodata
        nrows = src.height
        ncols = src.width

    scale_factor = 0.1
    # Save output as COG
    output_profile = dict(
        driver="GTiff",
        dtype=np.float32,
        count=1,
        height=nrows,
        width=ncols,
        crs=CRS.from_epsg(4326),
        transform=transform,
        nodata=np.float32(nodata_value) * scale_factor,
        tiled=True,
        compress="deflate",
        blockxsize=256,
        blockysize=256,
    )
    print("profile h/w: ", output_profile["height"], output_profile["width"])
    with MemoryFile() as memfile:
        with memfile.open(**output_profile) as mem:
            mem.write(variable[:].astype("float32") * scale_factor, indexes=1)
        cog_translate(
            memfile,
            f"{os.path.splitext(src_path)[0]}_cog.tif",
            output_profile,
            config=dict(GDAL_NUM_THREADS="ALL_CPUS", GDAL_TIFF_OVR_BLOCKSIZE="128"),
        )


to_cog(**f1)
