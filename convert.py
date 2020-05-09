import h5py
from osgeo import osr, gdal

# 0.25 degree files
# filename = 'OMI-Aura_L3-OMNO2d_2020m0101_v003-2020m0330t173100.he5'
# filename = '2020_01_01_NO2TropCS30.hdf5'
# hdf_file = h5py.File(filename)
# no2trop = hdf_file['HDFEOS']['GRIDS']['ColumnAmountNO2']['Data Fields']['ColumnAmountNO2TropCloudScreened']

# 0.1 degree file
filename = '2020_01_01_NO2TropCS30_Col3_V4.hdf5'
hdf_file = h5py.File(filename)
no2trop = hdf_file['NO2.COLUMN.VERTICAL.TROPOSPHERIC.CS30_BACKSCATTER.SOLAR'][:]
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
output_raster.GetRasterBand(1).SetNoDataValue(-1.26765E+30)

srs = osr.SpatialReference()
srs.ImportFromEPSG(4326)

output_raster.SetProjection(srs.ExportToWkt())

output_raster.FlushCache()
output_raster = None
