FROM lambgeo/lambda:gdal3.0-py3.7

ENV PACKAGE_PREFIX=/var/task

RUN pip install numpy rasterio argparse --no-binary :all: -t ${PACKAGE_PREFIX}/
RUN pip install h5py -t ${PACKAGE_PREFIX}/
RUN export CPLUS_INCLUDE_PATH=/usr/include/gdal  # path from `gdal-config --cflags`
RUN export C_INCLUDE_PATH=/usr/include/gdal
RUN pip install GDAL==$(gdal-config --version | awk -F'[.]' '{print $1"."$2}')
RUN yum install wget -y
COPY handler.py ${PACKAGE_PREFIX}/handler.py
COPY run.sh ${PACKAGE_PREFIX}/run.sh

