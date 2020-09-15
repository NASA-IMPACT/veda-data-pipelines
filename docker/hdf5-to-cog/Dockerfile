FROM osgeo/gdal:latest

RUN apt-get update
RUN apt-get upgrade -y

# Install Python & spatial libraries
RUN apt-get install python3-pip wget -y
RUN pip3 install rasterio netCDF4 rio-cogeo h5py boto3 requests

COPY run.py run.py