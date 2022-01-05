FROM osgeo/gdal:ubuntu-small-3.1.0

ARG EARTHDATA_USERNAME
ARG EARTHDATA_PASSWORD

RUN apt update && apt upgrade -y

# Install Python & spatial libraries
RUN apt-get install python3-pip wget -y
RUN echo machine urs.earthdata.nasa.gov login $EARTHDATA_USERNAME password $EARTHDATA_PASSWORD > ~/.netrc
COPY . code/

WORKDIR code
RUN pip3 install -r requirements.txt

