#!/bin/sh

# Enable command echo
set -v

# Directory where this script is located
CURR_DIR=`pwd`

# Icarus main folder
ICARUS_DIR=${CURR_DIR}/../..

# Dir where plots will be saved 
PLOTS_DIR=${CURR_DIR}/plots

# Config file
CONFIG_FILE=${CURR_DIR}/config.py

# FIle where results will be saved
RESULTS_FILE=${CURR_DIR}/results.pickle

# Add Icarus code to PYTHONPATH
export PYTHONPATH=${ICARUS_DIR}:$PYTHONPATH

# Run experiments
echo "Run experiments"
python ${ICARUS_DIR}/icarus.py --results ${RESULTS_FILE} ${CONFIG_FILE}

# Plot results
echo "Plot results"
python ${CURR_DIR}/plotresults.py --results ${RESULTS_FILE} --output ${PLOTS_DIR} ${CONFIG_FILE} 