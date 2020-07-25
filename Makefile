SHELL = /bin/bash -euo pipefail

DOC_DIR = doc

PYTHON_VERSION ?= 3.8

.PHONY: install test doc doc-clean doc-upload clean dist-clean build-container docker-shell

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
	python -m pytest icarus

# Build HTML documentation
doc: doc-clean
	make -C $(DOC_DIR) html

# Clean documentation
doc-clean:
	make -C $(DOC_DIR) clean

# Upload documentation to Icarus website
# requires write permissions to icarus-sim/icarus-sim.github.io
doc-upload:
	make -C $(DOC_DIR) upload

# Delete temp files
clean: doc-clean dist-clean
	find . -name "*.py[cod]" -o -name "*__pycache__" | xargs rm -rf

# Delete build files
dist-clean:
	rm -rf icarus.egg-info MANIFEST dist
