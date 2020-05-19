from pyhdf.SD import SD, SDC
from affine import Affine
from rasterio.crs import CRS
from rasterio.io import MemoryFile
from rio_cogeo.cogeo import cog_translate
from rio_cogeo.profiles import cog_profiles
import numpy as np
import argparse
from xml.etree.ElementTree import ElementTree
import re

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
  src_path=args.filename,
  variable_name="Optical_Depth_047"
)

hdf = SD(f1['src_path'], SDC.READ)
variable = hdf.select(f1['variable_name'])[0][:]
# Not sure how else to get this value at this time.
nodata_value = variable.min()

# Get latitude / longitude bounds from metadata
metadata_strings = hdf.attributes()['ArchiveMetadata.0'].split('\n\n')
metadata_dict = dict()
for metadata_string in metadata_strings:
    if 'OBJECT' in metadata_string:
        key_matches = re.search('OBJECT += (.+)$', metadata_string)
        value_matches = re.search('VALUE += (.+)\n', metadata_string)
        if key_matches and value_matches:
          metadata_dict[key_matches.group(1)] = value_matches.group(1)

xmin, ymin, xmax, ymax = [
  float(metadata_dict['WESTBOUNDINGCOORDINATE']),
  float(metadata_dict['SOUTHBOUNDINGCOORDINATE']),
  float(metadata_dict['EASTBOUNDINGCOORDINATE']),
  float(metadata_dict['NORTHBOUNDINGCOORDINATE'])
]

# Get latitude / longitude from XML
# Note: this seems problematic. At least in one case, one of the bounds
# was much different in the metadata from the `bounding coordinate` (e.g.
# longitudinal bounding coordinates were 179 + 172 but the minimum latitude in
# the XML metadata was -179.
#tree = ElementTree()
#xml = tree.parse(f"{f1['src_path']}.xml")
#print(xml)
#points = list(xml.find('GranuleURMetaData/SpatialDomainContainer/HorizontalSpatialDomainContainer/GPolygon/Boundary'))
#lon = list(map(lambda p: float(p.find('PointLongitude').text), points))
#lat = list(map(lambda p: float(p.find('PointLatitude').text), points))
#xmin, ymin, xmax, ymax = [min(lon), min(lat), max(lon), max(lat)]

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

# Review: should other parameters of the src profile be different than the
# output profile?
src_profile = output_profile
src_profile['crs'] = '+proj=sinu +lon_0=0 +x_0=0 +y_0=0 +a=6371007.181 +b=6371007.181 +units=m +no_defs'

print("profile h/w: ", output_profile["height"], output_profile["width"])
with MemoryFile() as memfile:
    with memfile.open(**src_profile) as mem:
        mem.write(variable, indexes=1)
    cog_translate(
        memfile,
        f"{f1['src_path']}.tif",
        output_profile,
        config=dict(GDAL_NUM_THREADS="ALL_CPUS", GDAL_TIFF_OVR_BLOCKSIZE="128"),
    )
