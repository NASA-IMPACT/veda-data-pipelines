# https://gdal.org/programs/gdal_translate.html
gdal_translate -of GTiff -a_srs '+proj=utm +zone=32S +datum=WGS84' \
  'HDF5:"L2GCOV_NASADEM_UTM-lopenp_14043_16008_009_160225_L090_CX_02.h5"://science/LSAR/GCOV/grids/frequencyA/HHHH' HHHH.tif

gdalwarp -s_srs '+proj=utm +zone=32S +datum=WGS84' -t_srs EPSG:3857 \
-srcnodata "nan" -dstnodata "-9999" \
-of COG -to SRC_METHOD=NO_GEOTRANSFORM HHHH.tif HHHH-reprojected.tif

# needs reprojection
# science_LSAR_GCOV_grids_frequencyA_projection_spatial_ref=PROJCS["WGS 84 / UTM zone 32S",GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4326"]],PROJECTION["Transverse_Mercator"],PARAMETER["latitude_of_origin",0],PARAMETER["central_meridian",9],PARAMETER["scale_factor",0.9996],PARAMETER["false_easting",500000],PARAMETER["false_northing",10000000],UNIT["metre",1,AUTHORITY["EPSG","9001"]],AXIS["Easting",EAST],AXIS["Northing",NORTH],AUTHORITY["EPSG","32732"]]