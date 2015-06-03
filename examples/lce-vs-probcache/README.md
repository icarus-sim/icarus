# Compare LCE and ProbCache strategies

This example compares LCE and ProbCache strategies using a sample RocketFuel topology.

## Run
To run the expriments and plot the results, execute the `run.sh` script:

    $ sh run.sh

## How does it work
The `config.py` contains all the configuration for executing experiments and
do plots. The `run.sh` script launches the Icarus simulator passing the configuration
file as an argument. The `plotresults.py` file provides functions for plotting
specific results based on `icarus.results.plot` functions.