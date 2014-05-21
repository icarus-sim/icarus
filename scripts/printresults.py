#!/usr/bin/env python
"""Print data from a resultset to the standard output.

Usage:
    python printresults.py <results-file.pickle>
"""
import argparse
from icarus.registry import results_reader_register

__all__ = ['print_results']

read = results_reader_register['PICKLE']

def print_results(path):
    """Print a resultset saved as pickle.
    
    Parameters
    ----------
    input : str
        The path to the pickled resultset
    """
    rs = read(path)
    n = len(rs)
    i = 0
    for experiment, results in rs:
        i += 1
        print("EXPERIMENT %d/%d:" % (i, n)) 
        print("  CONFIGURATION:")
        for k, v in experiment.iteritems():
            print("    * %s: %s" % (str(k), str(v)))
        print("  RESULTS:")
        for collector, data in results.iteritems():
            if isinstance(data, dict):
                print("    %s" % str(collector))
                for metric, value in data.iteritems():
                    print("     * %s: %s" % (str(metric), str(value)))
            else:
                print("     * %s: %s" % (str(collector), str(data)))
        print("")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="The simulation results file")
    args = parser.parse_args()
    print_results(args.input)

if __name__ == "__main__":
    main()
