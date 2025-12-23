# BPv7 DTN Node Simulation Container
#
# Based on NASA ION-DTN for interoperability testing
# Standards: CCSDS 734.20-O-1 / RFC 9171
#
FROM ubuntu:22.04

LABEL maintainer="SpeakUp Project"
LABEL description="BPv7 DTN Node for Space Network Simulation"

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    autoconf \
    automake \
    libtool \
    git \
    python3 \
    python3-pip \
    tcpdump \
    iproute2 \
    iputils-ping \
    net-tools \
    curl \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Clone and build ION-DTN (BPv7)
WORKDIR /opt
RUN git clone https://github.com/nasa-jpl/ION-DTN.git ion-dtn && \
    cd ion-dtn && \
    autoreconf -fi && \
    ./configure && \
    make && \
    make install && \
    ldconfig

# Copy our Python BPv7 implementation
COPY src/bpv7 /opt/bpv7

# Set up Python path
ENV PYTHONPATH=/opt

# Create DTN working directory
WORKDIR /dtn
RUN mkdir -p /dtn/sdr /dtn/config

# Default command
CMD ["bash"]
