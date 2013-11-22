# Icarus ICN caching simulator

Icarus is a Python-based simulator for evaluating the performance of in-network
caches in Information Centric Networks (ICN).

This document explains how to configure and run the simulator.

## Download and installation

### Prerequisites
Before using the simulator, you need to install all required dependencies.
If you use Ubuntu (version 13.10+) you can run the script `ubuntusetup.sh`
located in the `scripts` directory which will take of installing all the
dependencies.

Otherwise, you can install all dependencies manually. 
To use Icarus you need:

* Python interpreter (v 2.6 onwards, 2.7 preferred): you can either download it
  from the [Python website](http://www.python.org) or, possibly, from the package
  manager of your operating system.
* The following Python packages: 
   * numpy (versin 1.6 onwards)
   * scipy (version 0.12 onwards)
   * matplotlib (version 1.2 onwards)
   * networkx (version 1.6 onwards)
   * fnss (version 0.3 onwards)
   * argparse (only if using Python version 2.6. It is already included the standard
     library starting from Python 2.7)
  All these three packages are available on [PyPi](https://pypi.python.org/‎) and
  therefore can be installed using either `easy_install` or `pip` utilities.
  
  For example, assuming that you have pip, you can solve install all required
  packages by running:

  `pip install numpy scipy matplotlib networkx fnss`

  You may need to run pip as superuser. The installation of these packages,
  especially numpy and scipy may also require to install additional libraries.

### Download
After you have Python in place with all the required dependencies, you need to
download Icarus. You can get it by either cloning the Github repository,
running the following command from your command shell:

`git clone https://github.com/lorenzosaino/icarus.git`

or download the archive file of the repository and unpack it on your machine:
[\[zip\]](https://github.com/lorenzosaino/icarus/archive/master.zip) 
[\[tar.gz\]](https://github.com/lorenzosaino/icarus/archive/master.tar.gz)

### Configuration
Before being able to use it, you need to add the directory where this README
file is located to the PYTHONPATH environment variable

After all these things are taken care of you will be able to use Icarus.

## Usage

### Run simulations
To use Icarus with the currently implemented topologies and models of caching policies
and strategies you need to do the following.

1. Create a configuration file with all the desired parameters of your simulation
   You can modify the file `config.py`, which is well documented example configuration.
   You can even use the configuration file as it is just to get you started.
2. Run Icarus by running the script `icarus.py` using the following syntax

    `python icarus.py --output RESULTS_FILE [--plots PLOTS_DIR] CONF_FILE` 
   where:
    * `RESULTS_FILE` is the file in which results will be saved,
    * `PLOT_DIR` is the directory in which save the graphs of the results.
      This parameter is optional. If omitted, graphs will not be plotted. They
      can be plotted in a later stage anyway.
    * `CONF_FILE` is the configuration file

Example usage could be:

`python icarus.py --output results.pickle --plots graphs config.py`

By executing the steps illustrated above it is possible to run simulation using the
topologies, cache policies, strategies and result collectors readily available on
Icarus. Icarus makes it easy to implement new models to use in simulations. 

To implement new models, please refer to the description of the simulator 
provided in this paper:

L.Saino, I. Psaras and G. Pavlou, Icarus: a Caching Simulator for Information Centric
Networking (ICN), in Proc. of SIMUTOOLS'14, Lisbon, Portugal, March 2014.
[\[PDF\]](http://www.ee.ucl.ac.uk/~lsaino/publications/icarus-simutools14.pdf),
[\[BibTex\]](http://www.ee.ucl.ac.uk/~lsaino/publications/icarus-simutools14.bib)

Otherwise, please browse the source code. It is very well documented and easy to
understand.


## Citing

If you use Icarus for your paper, please refer to the following publication:

```
@inproceedings{icarus-simutools14,
     author = {Saino, Lorenzo and Psaras, Ioannis and Pavlou, George},
     title = {Icarus: a Caching Simulator for Information Centric Networking (ICN)},
     booktitle = {Proceedings of the 7th International ICST Conference on Simulation Tools and Techniques},
     series = {SIMUTOOLS '14},
     year = {2014},
     location = {Lisbon, Portugal},
     numpages = {10},
     publisher = {ICST},
     address = {ICST, Brussels, Belgium, Belgium},
}
```

## License
Icarus is licensed under the terms of the [GNU GPLv2 license](http://www.gnu.org/licenses/gpl-2.0.html).

## Reproduce results of previous papers

### Hash-routing paper (ACM SIGCOMM ICN '13)
This section explain how to reproduce the results and plot the graphs presented
in the paper:

L.Saino, I. Psaras and G. Pavlou, Hash-routing Schemes for Information Centric
Networking, in Proc. of the 3rd ACM SIGCOMM workshop on Information Centric
Networking (ICN'13), Hong Kong, China, August 2013.
[\[PDF\]](http://www.ee.ucl.ac.uk/~lsaino/publications/hashrouting-icn13.pdf),
[\[BibTex\]](http://www.ee.ucl.ac.uk/~lsaino/publications/hashrouting-icn13.bib)

To reproduce results and plot the graph, do the following:

1. Open your command shell
2. Move to the directory where this README file is contained and then to
  the subdirectory `./reproduce-results/hashrouting-icn13`
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

## Contacts
For further information about the Icarus simulator, please contact
[Lorenzo Saino](http://www.ee.ucl.ac.uk/~lsaino)

