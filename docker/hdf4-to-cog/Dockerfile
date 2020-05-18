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
RUN mkdir data
COPY MCD19A2.A2020134.h00v09.006.2020136042404.hdf data/MCD19A2.A2020134.h00v09.006.2020136042404.hdf
COPY handler.py handler.py
