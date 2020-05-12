import rasterio
import netCDF4 as nc
from rasterio.crs import CRS
import affine

import argparse


def handler(event, context):
    # Example dataset https://avdc.gsfc.nasa.gov/pub/data/satellite/Aura/OMI/V03/L3/OMNO2d_HR/OMNO2d_HRM/OMI_trno2_0.10x0.10_200410_Col3_V4.nc
    # Inputs
    filename = event["filename"]

    # Open netCDF file -- no file inspection and iteration --> rasterio
    with nc.Dataset(filename, "r") as src:
        variable = src.variables["TroposphericNO2"][:]
        lat = src.variables["LatitudeCenter"][:]
        lon = src.variables["LongitudeCenter"][:]

    # TODO throw error if given affine is the identity matrix
    # TODO consider case when lat lon give grid cell center
    xmin, ymin, xmax, ymax = [lon.min(), lat.min(), lon.max(), lat.max()]
    nrows, ncols = variable.shape[0], variable.shape[1]
    xres = (xmax - xmin) / float(ncols)
    yres = (ymax - ymin) / float(nrows)
    geotransform = (xmin, xres, 0, ymax, 0, -yres)

    # Write out file
    # TODO check for and set nodata
    # TODO make height and width more
    transform = affine.Affine.from_gdal(*geotransform)
    with rasterio.open(
        "./new2.tif",
        "w",
        driver="GTiff",
        height=nrows,
        width=ncols,
        count=1,
        dtype=variable.dtype,
        crs=CRS.from_epsg(4326),
        transform=transform,
    ) as f:
        f.write(variable[:], 1)

    print("Done")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate COG from netCDF file")
    parser.add_argument("-f", "--filename", help="netCDF filename to convert")
    args = parser.parse_args()
    print(args)
    event = {"filename": args.filename}
    handler(event, None)
