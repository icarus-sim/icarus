SHELL = /bin/sh

DOC_DIR = doc

.PHONY: init test docclean doc clean distclean

all: install

# Install all dependencies as well as Icarus in developer mode
install:
	pip install --upgrade pip setuptools
	pip install --upgrade -r requirements.txt
	pip install --upgrade -e .

# Run all test cases
test:
	py.test icarus

# Clean documentation
docclean:
	make -C $(DOC_DIR) clean

# Build HTML documentation
doc: docclean
	make -C $(DOC_DIR) html

# Delete temp files
clean: docclean distclean
	find . -name "*__pycache__" | xargs rm -rf
	find . -name "*.pyc" | xargs rm -rf

distclean:
	rm -rf icarus.egg-info MANIFEST
