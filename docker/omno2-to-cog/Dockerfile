FROM osgeo/gdal:ubuntu-small-3.1.0

RUN apt-get update
RUN apt-get upgrade -y

# Install Python & spatial libraries
RUN apt-get install python3-pip -y
RUN pip3 install rasterio rio-cogeo h5py

# Install CLI tools
RUN apt-get install wget -y
RUN pip3 install awscli

# Install URS credentials
ARG EARTHDATA_USERNAME
ARG EARTHDATA_PASSWORD
RUN echo machine urs.earthdata.nasa.gov login $EARTHDATA_USERNAME password $EARTHDATA_PASSWORD > ~/.netrc

# Copy context into container
WORKDIR /home
COPY OMNO2d_HR/handler.py OMNO2d_HR/handler.py
COPY OMNO2d.003/handler.py OMNO2d.003/handler.py
COPY run-cog-convert.sh run-cog-convert.sh
