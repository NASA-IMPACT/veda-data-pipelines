#!/bin/bash
wget -O hdf-4.2.15-osx1013_64-clang.tar.gz https://support.hdfgroup.org/ftp/HDF/releases/HDF4.2.15/bin/unix/hdf-4.2.15-osx1013_64-clang.tar.gz
tar zxvf hdf-4.2.15-osx1013_64-clang.tar.gz

export LIBRARY_DIRS=$(pwd)/HDF-4.2.15-Darwin/HDF_Group/HDF/4.2.15/lib
export INCLUDE_DIRS=$(pwd)/HDF-4.2.15-Darwin/HDF_Group/HDF/4.2.15/include

wget -O pyhdf-0.9.0.tar.gz https://hdfeos.org/software/pyhdf/pyhdf-0.9.0.tar.gz
tar zxvf pyhdf-0.9.0.tar.gz && cd pyhdf-0.9.0
python setup.py install

