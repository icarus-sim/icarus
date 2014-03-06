#!/bin/sh
#
# This script installs all Icarus dependencies
#
# It has been tested successfully only on Ubuntu 13.10+.
#
sudo apt-get install python ipython python-pip python-numpy python-scipy python-matplotlib python-nose python-sphinx
sudo pip install -U networkx fnss numpydoc