# Docker container for running Icarus
#
# Some useful commands:
#
# Build:        docker build -t icarus .
# Open shell:   docket run --rm -it icarus
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
ARG py_ver=2.7
FROM python:${py_ver}

COPY . /icarus
WORKDIR /icarus

RUN make install

CMD ["bash"]
