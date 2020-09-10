FROM osgeo/gdal:latest

RUN apt-get update
RUN apt-get upgrade -y

# Install Python & spatial libraries
RUN apt-get install python3-pip wget -y
RUN pip3 install rasterio netCDF4 rio-cogeo h5py boto3

ARG AWS_ACCESS_KEY_ID
ARG AWS_SECRET_ACCESS_KEY

# Store AWS credentials
RUN mkdir ~/.aws
RUN echo [default]\\nregion = us-east-1\\naws_access_key_id = $AWS_ACCESS_KEY_ID\\naws_secret_access_key = $AWS_SECRET_ACCESS_KEY > ~/.aws/credentials

COPY run.py run.py