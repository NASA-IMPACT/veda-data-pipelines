FROM osgeo/gdal:latest

RUN apt-get update
RUN apt-get upgrade -y

# Install Python & spatial libraries
RUN apt-get install python3-pip wget -y
RUN pip3 install -r requirements.txt

ARG AWS_ACCESS_KEY_ID
ARG AWS_SECRET_ACCESS_KEY

COPY run.py run.py