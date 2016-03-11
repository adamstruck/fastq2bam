FROM ubuntu:14.04

MAINTAINER strucka@ohsu.edu

LABEL version="0.0.1" \
      description="Convert paired-end fastq files to unaligned BAM with PCAWG style header using biobambam2"

USER root
RUN apt-get update \
    && apt-get dist-upgrade -y --force-yes \
    && apt-get install software-properties-common -y

RUN apt-get update && apt-get install -y --force-yes \
    build-essential \
    g++ \
    gcc \
    autoconf \
    automake \
    libtool \
    make \
    tar \
    gzip \
    pkg-config \
    libboost-all-dev \
    libgflags-dev \
    liblz4-dev \
    liblzo2-dev \
    libncurses5-dev \
    git \
    python \
    python-pip \
    time \
    wget \
    zlib1g-dev

RUN apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# setup
ENV HOME /home/
RUN mkdir ${HOME}/tools/
WORKDIR ${HOME}/tools/

# Download tools
RUN wget http://downloads.sourceforge.net/project/staden/io_lib/1.14.4/io_lib-1.14.4.tar.gz \
    && tar xf io_lib-1.14.4.tar.gz \
    && mv io_lib-1.14.4 io_lib \
    && rm *.gz
    
RUN wget https://github.com/google/snappy/releases/download/1.1.3/snappy-1.1.3.tar.gz \
    && tar xf snappy-1.1.3.tar.gz \
    && mv snappy-1.1.3 snappy \
    && rm *.gz

RUN git clone https://github.com/gt1/libmaus2.git libmaus2
RUN git clone https://github.com/gt1/biobambam2.git biobambam2

# snappy
WORKDIR ${HOME}/tools/snappy/
RUN ./configure --prefix=${HOME} && \
    make -j4 && \
    make install

# io_lib
WORKDIR ${HOME}/tools/io_lib/
RUN ./configure --prefix=${HOME} && \
    make -j4 && \
    make install

# Build libmaus
WORKDIR ${HOME}/tools/libmaus2
RUN libtoolize && \
    aclocal && \
    autoreconf -i -f && \
    ./configure --prefix=${HOME} && \
    make && \
    make install

# Build biobambam2
WORKDIR ${HOME}/tools/biobambam2
RUN autoreconf -i -f && \
    ./configure --with-libmaus2=${HOME} && \
    make && \
    make install 

# install python dependencies
RUN pip install python-dateutil

# add wrapper script and make it executable
COPY ./fastq2bam.py ${HOME}/fastq2bam.py
RUN chmod +x ${HOME}/fastq2bam.py

WORKDIR ${HOME}

VOLUME /output/

CMD /bin/bash
