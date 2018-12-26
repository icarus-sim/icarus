SHELL = /bin/bash

DOC_DIR = doc

PYTHON_VERSION ?= 3.7

.PHONY: install test doc docclean docupload clean distclean build-container docker-shell

all: install

build-container:
	docker build --build-arg PYTHON_VERSION=$(PYTHON_VERSION) -t icarus .

docker-shell: build-container
	docker run --rm -it icarus

# Install all dependencies as well as Icarus in developer mode
install:
	pip install --upgrade pip setuptools
	pip install --upgrade -r requirements.txt
	pip install --upgrade -e .

# Run all test cases
test:
	py.test icarus

# Build HTML documentation
doc: docclean
	make -C $(DOC_DIR) html

# Clean documentation
docclean:
	make -C $(DOC_DIR) clean

# Upload documentation to Icarus website
# requires write permissions to icarus-sim/icarus-sim.github.io
docupload:
	make -C $(DOC_DIR) upload

# Delete temp files
clean: docclean distclean
	find . -name "*__pycache__" | xargs rm -rf
	find . -name "*.pyc" | xargs rm -rf

# Delete build files
distclean:
	rm -rf icarus.egg-info MANIFEST dist
