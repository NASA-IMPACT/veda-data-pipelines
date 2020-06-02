FROM osgeo/gdal:ubuntu-small-3.1.0

RUN apt-get update
RUN apt-get upgrade -y

# Install Python & spatial libraries
RUN apt-get install python3-pip -y
RUN pip3 install rio-cogeo

RUN pip3 install awscli

COPY handler.py handler.py
COPY run.sh run.sh
