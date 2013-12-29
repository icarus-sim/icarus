#!/usr/bin/env python
"""This script runs the Icarus simulator.

It automatically adds Icarus source folder to the PYTHONPATH and then
executes the simulator according to the settings specified in the provided 
configuration file.
"""
import sys
from os import path
import argparse

def main():
    src_dir = path.abspath(path.dirname(__file__))
    sys.path.insert(0, src_dir)
    import icarus.run
    import icarus.results.plot
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-r", "--results", dest="results",
                        help='the file on which results will be saved',
                        required=True)
    parser.add_argument("-p", "--plots", dest="plotsdir",
                        help='plot results and save them in plotsdir',
                        required=False)
    parser.add_argument("config",
                        help="configuration file")
    args = parser.parse_args()
    icarus.run.run(args.config, args.results)
    if args.plotsdir:
        icarus.results.plot.run(args.config, args.results, args.plotsdir)

if __name__ == "__main__":
    main()
