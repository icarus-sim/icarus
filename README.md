# Icarus ICN caching simulator

Icarus is a Python-based simulator for evaluating the performance of in-network
caches in Information Centric Networks (ICN).

This document explains how to configure and run the simulator.

## Install
To use the simulator, you need:

* Python (v 2.6 onwards, 2.7 preferred): you can either download it from the
  [Python website](http://www.python.org) or, possibly, from the package manager of your
  operating system
* Python packages: networkx, numpy, fnss. All these three packages are available
  on [PyPi](https://pypi.python.org/‎) and therefore can be installed using
  either `easy_install` or `pip`.
  
After you have Python in place with all the required dependencies, you need to
download Icarus. You can get it by either cloning the Github repository,
running the following command from your command shell:

`git clone https://github.com/lorenzosaino/icarus.git`

or download the archive file of the repository and unpack it on your machine:
[zip](https://github.com/lorenzosaino/icarus/archive/master.zip) 
[tar.gz](https://github.com/lorenzosaino/icarus/archive/master.tar.gz)

Before being able to use it, you need to add the directory where this README
file is located to the PYTHONPATH environment variable.

After all these things are taken care of you will be able to use Icarus.

## Reproduce results of hash-routing paper (ACM SIGCOMM ICN '13)
This section explain how to reproduce the results and plot the graphs presented
in the paper:

L.Saino, I. Psaras and G. Pavlou, Hash-routing Schemes for Information Centric
Networking, in Proc. of the 3rd ACM SIGCOMM workshop on Information Centric
Networking (ICN'13), Hong Kong, China, August 2013.
[\[PDF\]](http://www.ee.ucl.ac.uk/~lsaino/publications/hashrouting-icn13.pdf),
[\[BibTex\]](http://www.ee.ucl.ac.uk/~lsaino/publications/hashrouting-icn13.bib)

To reproduce results and plot the graph, do the following:

1. Open your command shell
2. Move to the directory where this README file is contained
3. Execute the command `sh reproduce_hashrouting_icn13_results.sh`

This will run all simulations automatically, save all log files and plot all
paper graphs.

The logs will be saved in the `logs` directory, while the graphs will be saved
in the `graphs` directory.

This script has been tested only on Ubuntu 12.04.

If you want to change the configuration of the program, e.g. the range of
parameters tested, the number of CPU cores used and so on, please look at the 
file `icarus/config.py`. It contains all the configuration parameters and it is
well commented.

## Run with customized parameters
To use this simulator for gathering results about caching performance wuthout
using the script provided, you need to carry out three tasks:

1. Generate the scenarios, i.e. generate the topology and, possibly, event
   schedule files for all the configurations you want to run
2. Run the actual simulations, once per each set of configuration parameters
3. Plot/analyse the results

To generate the scenarios, you can simply run the file `scenario.py` located in
the directory `./icarus` with the parameters already configured. Do:

`cd icarus`

`python scenario.py`

If you wish to use different parameters, go and edit the relevant variables in
`scenario.py`. All scenarios are stored in directory `./scenarios`.

To run the actual simulations, run the file `scenario.py` located in the directory `./icarus`.

`cd icarus`

`python exec.py`

Notice two things: if you open the file you see some configuration variables
that you can change. In particular:

* `generate_scenarios`
* `logging.LOG_EVERYTHING`

By setting generate_scenarios to `True`, Icarus automatically generates the
scenario files, otherwise, it assumes that the folder `./scenarios` already
contains the topology files.

`logging.LOG_EVERYTHING` allows you to enable/disable generation of detailed logs.
All logs are stored in the directory `./logs`.
If this variable is set to False, the simulator will create only two summary
files: `SUMMARY_CACHE_HIT_RATIO.txt` and `SUMMARY_NETWORK_LOAD.txt` which
contain one line per scenario run. If this variable is set to True, then each
event of the simulation (cache and link events) will be saved.
These file may become very large, in the order of hundreds of GB.

## Log file specifications
For each single scenario run, if `logging.LOG_EVERYTHING` configuration
variable is set to `True`, the the simulator generates four log files:

* `RESULTS_SCENARIO-ID_CACHE.txt`: Tab-separated values, one line per cache event (cache hit, server hit etc..)
* `RESULTS_SCENARIO-ID_LINK.txt`: Tab-separated values, one line per link event (link X traversed by content Y at time Z etc..)
* `RESULTS_SCENARIO-ID_STRETCH.txt` (off-path strategies only): Tab-separated values, path stretch for each content retrieval (useful for plotting stretch CDF)
* `RESULTS_SCENARIO-ID_DELAY.txt` (no cache and CEE+LRU strategies only): Tab-separated values, RTT for each content retrieval (useful for plotting RTT CDF)

In addition, regardless of the value of `logging.LOG_EVERYTHING`, there
simulator generates two summary files:

* `SUMMARY_CACHE_HIT_RATIO.txt`: each line reports the overall cache hit ratio of a single experiment
* `SUMMARY_NETWORK_LOAD.txt`: each line reports the overall link load of a single experiment

Each single experiment appends a line to each of these two files.

## Contacts
For further information about the Icarus simulator, please contact
[Lorenzo Saino](http://www.ee.ucl.ac.uk/~lsaino)

