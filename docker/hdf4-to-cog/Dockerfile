FROM continuumio/miniconda3

WORKDIR /home
ENV HDF4_SRC hdf-4.2.15
ENV HDF4_SRC_FILENAME ${HDF4_SRC}.tar.gz
RUN wget -O $HDF4_SRC_FILENAME https://support.hdfgroup.org/ftp/HDF/releases/HDF4.2.15/src/$HDF4_SRC_FILENAME && \
  tar zxvf $HDF4_SRC_FILENAME
ENV LIBRARY_DIRS /home/$HDF4_SRC/lib
ENV INCLUDE_DIRS /home/$HDF4_SRC/include

RUN conda install numpy
RUN conda install -c conda-forge pyhdf
RUN pip install rio-cogeo

ARG EARTHDATA_USERNAME
ARG EARTHDATA_PASSWORD
RUN echo machine urs.earthdata.nasa.gov login $EARTHDATA_USERNAME password $EARTHDATA_PASSWORD > ~/.netrc

RUN apt-get instally -y libgdal-dev
RUN pip install gdal

COPY handler.py handler.py
COPY run.sh run.sh
