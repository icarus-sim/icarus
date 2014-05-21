#!/bin/sh
#
# Reproduce results of ACM SIGCOMM ICN'13 hash-routing paper
#

echo "ADDING ICARUS TO PYTHON PATH"
export PYTHONPATH=`pwd`:$PYTHONPATH
echo "CREATING DIRECTORIES FOR GRAPHS AND LOGS"
mkdir -p logs
mkdir -p graphs
cd icarus
echo "EXECUTING SIMULATIONS"
python run.py
echo "PLOTTING RESULTS"
python plot.py
echo "DONE"
