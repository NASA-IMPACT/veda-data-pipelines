FROM osgeo/gdal:ubuntu-small-3.1.0

RUN apt-get update
RUN apt-get upgrade -y

# Install Python & spatial libraries
RUN apt-get install python3-pip -y
RUN pip3 install rasterio netCDF4 rio-cogeo

# Install CLI tools
RUN apt-get install wget -y
RUN pip3 install awscli

# Copy context into container
COPY handler.py /home/handler.py
COPY run-cog-convert.sh /home/run-cog-convert.sh
