# Reproduce results of hash-routing paper (ACM SIGCOMM ICN '13)
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
3. Execute the command `sh reproduce_results.sh`

This will run all simulations automatically, save all log files and plot all
paper graphs.

The logs will be saved in the `logs` directory, while the graphs will be saved
in the `graphs` directory.

This script has been tested only on Ubuntu 12.04.

If you want to change the configuration of the program, e.g. the range of
parameters tested, the number of CPU cores used and so on, please look at the 
file `icarus/config.py`. It contains all the configuration parameters and it is
well commented.

**ATTENTION**: The code used to reproduce the results of the hash-routing
paper is based on an older version of Icarus which, although well tested,
it is poorly documented and difficult to extend.
This code should therefore be used only to reproduce the results shown in the
paper. If you wish to run simulations using different parameters or implement
new models, you should use the latest version of the code located in the main
directory.

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
