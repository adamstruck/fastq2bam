FROM ubuntu:14.04

MAINTAINER strucka@ohsu.edu

LABEL version="0.0.1" \
      description="Convert paired-end fastq files to unaligned BAM with PCAWG style header using biobambam2"

USER root

RUN apt-get update && apt-get install -y --force-yes \
    build-essential \
    g++ \
    gcc \
    autoconf \
    automake \
    libtool \
    pkg-config \
    make \
    libboost-all-dev \
    libgflags-dev \
    liblz4-dev \
    liblzo2-dev \
    libncurses5-dev \
    zlib1g-dev \
    tar \
    gzip \
    git \
    python \
    python-pip \
    python-dateutil \
    time \
    wget \
    curl

RUN apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Install biobambam2 - 2.0.44
WORKDIR /tmp/
RUN curl -ksSL -o tmp.tar.gz --retry 10 https://github.com/gt1/biobambam2/releases/download/2.0.44-release-20160517104101/biobambam2-2.0.44-release-20160517104101-x86_64-etch-linux-gnu.tar.gz && \
    tar --strip-components 1 -zxf tmp.tar.gz && \
    cp -r bin/* /usr/local/bin/. && \
    cp -r etc/* /usr/local/etc/. && \
    cp -r lib/* /usr/local/lib/. && \
    cp -r share/* /usr/local/share/. && \
    rm -rf *

# install python dependencies
RUN pip install pytz

# add wrapper script and make it executable
COPY ./fastq2bam.py /usr/local/bin/fastq2bam.py
RUN chmod +x /usr/local/bin/fastq2bam.py

WORKDIR /output/
VOLUME /output/
CMD /bin/bash
