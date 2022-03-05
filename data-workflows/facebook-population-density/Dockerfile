FROM osgeo/gdal AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y python3-pip
RUN pip install --upgrade pip
RUN pip --no-cache-dir install --upgrade awscli

RUN pip install rio-cogeo==2.3.1
COPY generate_cog_and_upload.sh .

ENTRYPOINT ["./generate_cog_and_upload.sh"]
