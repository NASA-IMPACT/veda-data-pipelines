import h5py
import rasterio
from rasterio.crs import CRS
import affine

import argparse


def handler(event, context):
    # Inputs
    filename = event["filename"]
    variable_dataset = "NO2.COLUMN.VERTICAL.TROPOSPHERIC.CS30_BACKSCATTER.SOLAR"
    # 0.1 degree file

    # Open HDF file
    with h5py.File(filename, "r") as hdf_file:
        if not variable_dataset in hdf_file.keys():
            raise KeyError("Variable dataset not found in HDF file")
        variable = hdf_file[variable_dataset][:]
        lat = hdf_file["LATITUDE"][:]
        lon = hdf_file["LONGITUDE"][:]

    # Calculate transform
    xmin, ymin, xmax, ymax = [lon.min(), lat.min(), lon.max(), lat.max()]
    nrows, ncols = variable.shape
    xres = (xmax - xmin) / float(ncols)
    yres = (ymax - ymin) / float(nrows)
    geotransform = (xmin, xres, 0, ymax, 0, -yres)
    # TODO investigate an affine that works for swath datasets

    # Write out file
    transform = affine.Affine.from_gdal(*geotransform)
    with rasterio.open(
        "./new2.tif",
        "w",
        driver="GTiff",
        height=variable.shape[0],
        width=variable.shape[1],
        count=1,
        dtype=variable.dtype,
        crs=CRS.from_epsg(4326),
        transform=transform,
    ) as f:
        f.write(variable[:], 1)

    print("Done")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate COG from HDF5 file")
    parser.add_argument("-f", "--filename", help="HDF5 filename to convert")
    args = parser.parse_args()
    print(args)
    event = {"filename": args.filename}
    handler(event, None)
