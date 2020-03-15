# Docker container for running Icarus
#
# Some useful commands:
#
# Build:        docker build [--build-arg PYTHON_VERSION=<python-version>] -t icarus .
# Open shell:   docker run --rm -it icarus
# Run command:  docker run icarus <COMMAND>
#
# To run a simulation with Icarus it is advisable to mount in the container
# the directories where the config file is located and where you intend
# to store results and access them from the container.
#
# For example, to use config.py and store the result file in the root of the project
# you could run the container with the following command:
#
# docker run -v `pwd`:/data icarus icarus run -r /data/results.pickle /data/config.py
#
ARG PYTHON_VERSION=3.8
FROM python:${PYTHON_VERSION}

# Uncomment the following line to use pypy3. Building numpy and scipy on pypy3 is very slow.
# FROM pypy:3

RUN apt-get update \
  && apt-get install -y -q \
    gfortran \
    graphviz \
    libatlas-base-dev \
    libatlas-dev \
    libgdal-dev \
    liblapack-dev \
    libsuitesparse-dev \
    mono-devel \
  && rm -rf /var/lib/apt/lists/*

COPY . /icarus
WORKDIR /icarus

RUN make install

CMD ["bash"]
