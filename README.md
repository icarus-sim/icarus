# Icarus ICN caching simulator

Icarus is a Python-based simulator for evaluating the performance of in-network
caches in Information Centric Networks (ICN).

This document explains how to configure and run the simulator. 

## Install
To use the simulator, you need:

* Python (v 2.6 onwards, 2.7 preferred): you can either download it from the
  [Python website](http://www.python.org) or, possibly, from the package manager of your
  operating system
* Python packages: networkx, numpy, fnss. All these three packages are available on PyPi
  and therefore can be installed using `easy_install` or `pip`.

Before being able to use it, you need to add the directory where this file is located to
the PYTHONPATH environment variable.

After all these things are taken care you should be able to use it.

# Reproduce results of SIGCOMM ICN '13
To reproduce results, run the script:

`./reproduce_sigcomm_icn_13_results.sh`

This will do everything automatically.

# Run with modified parameters
To use this simulator for gathering results about caching performance, you need to carry out three tasks:

1. Generate the scenarios, i.e. generate the topology and, possibly, event schedule files for all the
   configurations you want to run
2. Run the actual simulations, once per each set of configuration parameters
3. Plot/analyse the results

To generate the scenarios, you can simply run the file `scenario.py` located in the directory `./icarus`
with the parameters already configured. Do:

`cd icarus`

`python scenario.py`

If you wish to use different parameters, go and edit the relevant variables in `scenario.py`.
The scenarios are stored in directory `./scenarios`.

To run the actual simulations, run the file `scenario.py` located in the directory `./icarus`.

`cd icarus`

`python exec.py`

Notice two things: if you open the file you see some configuration variables that you can change. In particular:

* `generate_scenarios`
* `logging.LOG_EVERYTHING`

By setting generate_scenarios to `True`, Icarus automatically generates the scenario files, otherwise, it assumes
that the folder `./scenarios` already contains the topology files.

`logging.LOG_EVERYTHING` allows you to enable/disable generation of detailed logs.
All logs are stored in the directory `./logs`.
If this variable is set to False, the simulator will create only two summary files: `SUMMARY_CACHE_HIT_RATIO.txt`
and `SUMMARY_NETWORK_LOAD.txt` which contain one line per scenario run.
If this variable is set to True, then each event of the simulation (cache and link events) will be saved.
These file may become very large, in the order of hundreds of GB.

# Log file specifications
Each single scenario, generates three files:

* `RESULTS_SCENARIO-ID_CACHE.txt`: Tab-separated values, one line per cache event (cache hit, server hit etc..)
* `RESULTS_SCENARIO-ID_LINK.txt`: Tab-separated values, one line per link event (link X traversed by content Y at time Z etc..)
* `RESULTS_SCENARIO-ID_STRETCH.txt` (off-path strategies only): Tab-separated values, path stretch for each content retrieval (useful for plotting stretch CDF)

In addition, there are two summary files:

* `SUMMARY_CACHE_HIT_RATIO.txt`: each line reports the overall cache hit ratio of a single experiment
* `SUMMARY_NETWORK_LOAD.txt`: each line reports the overall link load of a single experiment
Each single experiment appends a line to each of these two files.
