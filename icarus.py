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
    from icarus import __version__
    from icarus.run import run
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-r", "--results", dest="results",
                        help='the file on which results will be saved',
                        required=True)
    parser.add_argument("-c", "--config-override", dest="config_override", action="append",
                        help='override specific key=value parameter of configuration file',
                        required=False)
    parser.add_argument("config",
                        help="configuration file")
    parser.add_argument('--version', action='version',
                        version="icarus %s" % __version__)
    args = parser.parse_args()
    config_override = dict(c.split("=") for c in args.config_override) \
             if args.config_override else None
    run(args.config, args.results, config_override)


if __name__ == "__main__":
    main()
