SHELL = /bin/sh

DOC_DIR = doc

.PHONY: run test docclean doc clean

all: run

# Run Icarus with default configuration
run:
	python icarus.py --results results.pickle config.py

# Run all test cases
test:
	python test.py

# Clean documentation
docclean:
	cd $(DOC_DIR); make clean

# Build HTML documentation
doc: docclean
	cd $(DOC_DIR); make html

# Delete temp files
clean: docclean
	find . -name "*__pycache__" | xargs rm -rf
	find . -name "*.pyc" | xargs rm -rf