FROM centos/python-36-centos7

RUN apt-get update -y
RUN apt-get install -y wget

WORKDIR /home
ENV HDF4_SRC hdf-4.2.15-linux-centos7-x86_64-shared
ENV HDF4_SRC_FILENAME ${HDF4_SRC}.tar.gz
RUN wget -O $HDF4_SRC_FILENAME https://support.hdfgroup.org/ftp/HDF/releases/HDF4.2.15/bin/unix/$HDF4_SRC_FILENAME && \
  tar zxvf $HDF4_SRC_FILENAME
ENV LIBRARY_DIRS /home/$HDF4_SRC/lib
ENV INCLUDE_DIRS /home/$HDF4_SRC/include
RUN ls

RUN wget -O pyhdf-0.9.0.tar.gz https://hdfeos.org/software/pyhdf/pyhdf-0.9.0.tar.gz && \
  tar zxvf pyhdf-0.9.0.tar.gz && cd pyhdf-0.9.0
WORKDIR /home/pyhdf-0.9.0
RUN pip install numpy
RUN python setup.py install

