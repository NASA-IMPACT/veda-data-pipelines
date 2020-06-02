FROM continuumio/miniconda3

# Install python libraries
RUN conda install numpy
RUN pip install rio-cogeo

RUN pip install awscli

COPY run.sh run.sh
