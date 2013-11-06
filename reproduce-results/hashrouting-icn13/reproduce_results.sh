#!/bin/sh
#
# Reproduce SIGCOMM ICN 13 results:
#

echo "ADDING ICARUS TO PYTHON PATH"
export PYTHONPATH=`pwd`:$PYTHONPATH
echo "CREATING DIRECTORIES FOR GRAPHS AND LOGS"
mkdir -p logs
mkdir -p graphs
cd icarus
echo "EXECUTING SIMULATIONS"
#python run.py
echo "PLOTTING RESULTS"
python plot.py
echo "DONE"
