FROM ubuntu:14.04

MAINTAINER strucka@ohsu.edu

LABEL version="0.0.1" \
      description="Convert paired-end fastq files to unaligned BAM with PCAWG style header using biobambam2"

USER root

WORKDIR /home
RUN apt-get -yqq update && \
    apt-get -yqq install build-essential \
			 					 				 zlib1g-dev \
												 pkg-config \
								 				 autoconf \
												 automake \
												 libtool \
												 wget \
												 git \
								 				 libncurses5-dev \
												 python \
												 tar \
												 gzip \
												 libboost-dev && \
    apt-get clean

RUN git clone https://github.com/gt1/libmaus2.git libmaus && \
    git clone https://github.com/gt1/biobambam2.git biobambam

# Build libmaus
WORKDIR /home/libmaus
RUN libtoolize && \
		aclocal && \
		autoreconf -i -f && \
		./configure && \
    make && \
		make install

# Build biobambam2
WORKDIR /home/biobambam
RUN autoreconf -i -f && \
    ./configure --with-libmaus2=/usr/local/ && \
    make && \
		make install

# install python dependencies
RUN apt-get install -yqq python-pip 
RUN pip install python-dateutil

# add wrapper script and make it executable
COPY ./fastq2bam.py /home/fastq2bam.py
RUN chmod +x  /home/fastq2bam.py

WORKDIR /home/

VOLUME /output/

CMD /bin/bash
