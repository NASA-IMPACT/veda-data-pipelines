import h5py
from osgeo import osr, gdal
import argparse

def handler(event, context):
    # 0.1 degree file
    filename = event['filename']
    hdf_file = h5py.File(filename)
    no2trop = hdf_file['NO2.COLUMN.VERTICAL.TROPOSPHERIC.CS30_BACKSCATTER.SOLAR']
    lat = hdf_file['LATITUDE'][:]
    lon = hdf_file['LONGITUDE'][:]

    xmin, ymin, xmax, ymax = [lon.min(), lat.min(), lon.max(), lat.max()]
    nrows,ncols = no2trop.shape
    xres = (xmax-xmin) / float(ncols)
    yres = (ymax-ymin) / float(nrows)
    geotransform = (xmin, xres, 0, ymax, 0, -yres) 

    output_raster = gdal.GetDriverByName('GTiff').Create(f'{filename}.tif', ncols, nrows, 1, gdal.GDT_Float64)  # Open the file
    output_raster.SetGeoTransform(geotransform)
    output_raster.GetRasterBand(1).WriteArray(no2trop[:])
    output_raster.GetRasterBand(1).SetNoDataValue(no2trop.fillvalue)

    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)
    output_raster.SetProjection(srs.ExportToWkt())

    output_raster.FlushCache()
    output_raster = None
    print('Done')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate COG from HDF5 file')
    parser.add_argument('-f', '--filename', help='HDF5 filename to convert')
    args = parser.parse_args()
    print(args)
    event = {'filename': args.filename}
    handler(event, None)

