#!/bin/sh
#
# Reproduce SIGCOMM ICN 13 results:
#

echo "ADDING ICARUS TO PYTHON PATH"
export PYTHONPATH=$PYTHONPATH:`pwd`
cd icarus
echo "EXECUTING SIMULATIONS"
python run.py
echo "PLOTTING RESULTS"
python plot.py
echo "DONE"
