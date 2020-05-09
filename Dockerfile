FROM lambgeo/lambda:gdal3.0-py3.7

ENV PACKAGE_PREFIX=/var/task

RUN yum install -y python-devel
RUN pip install numpy rasterio --no-binary :all: -t ${PACKAGE_PREFIX}/
RUN pip install h5py argparse --no-binary :all: -t ${PACKAGE_PREFIX}/

COPY handler.py ${PACKAGE_PREFIX}/handler.py
COPY run.sh ${PACKAGE_PREFIX}/run.sh

