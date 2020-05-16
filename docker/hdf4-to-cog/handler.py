from pyhdf.SD import SD, SDC
from affine import Affine
from rasterio.crs import CRS
from rasterio.io import MemoryFile
from rio_cogeo.cogeo import cog_translate
from rio_cogeo.profiles import cog_profiles
import numpy as np

src_path = 'data/MCD19A2.A2020134.h00v08.006.2020136040432.hdf'
hdf = SD(src_path, SDC.READ)
variable = hdf.select('Optical_Depth_047')[0][:]
nodata_value = variable.min()
EASTBOUNDINGCOORDINATE=-169.991666651401
NORTHBOUNDINGCOORDINATE=9.99999999910196
SOUTHBOUNDINGCOORDINATE=0.0
WESTBOUNDINGCOORDINATE=-179.999999983835
xmin, ymin, xmax, ymax = [
  WESTBOUNDINGCOORDINATE,
  SOUTHBOUNDINGCOORDINATE,
  EASTBOUNDINGCOORDINATE,
  NORTHBOUNDINGCOORDINATE
]
nrows, ncols = variable.shape[0], variable.shape[1]
xres = (xmax - xmin) / float(ncols)
yres = (ymax - ymin) / float(nrows)
geotransform = (xmin, xres, 0, ymax, 0, -yres)
dst_transform = Affine.from_gdal(*geotransform)

# Save output as COG
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
print("profile h/w: ", output_profile["height"], output_profile["width"])
with MemoryFile() as memfile:
    with memfile.open(**output_profile) as mem:
        mem.write(variable, indexes=1)
    cog_translate(
        memfile,
        f"{src_path}.tif",
        output_profile,
        config=dict(GDAL_NUM_THREADS="ALL_CPUS", GDAL_TIFF_OVR_BLOCKSIZE="128"),
    )
