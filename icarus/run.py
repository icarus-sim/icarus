#!/usr/bin/env python
"""Launches a simulation campaign and save results.
"""
import sys
import os
import signal
import argparse
import functools
import logging

from icarus.util import Settings, config_logging
from icarus.registry import results_writer_register
from icarus.orchestration import Orchestrator
from icarus.results import plot


__all__ = ['run', 'handler']


logger = logging.getLogger('main')


def handler(settings, orch, output, signum=None, frame=None):
    """Signal handler
    
    This function is called when the simulator receive SIGTERM, SIGHUP, SIGKILL
    or SIGQUIT from the OS.
    
    Its function is simply to write on a file the partial results.
    
    Parameters
    ----------
    settings : Settings
        The simulator settings
    orch : Orchestrator
        The instance of the orchestrator
    output : str
        The output file
    """
    logger.error('Received signal %d. Terminating' % signum)
    results_writer_register[settings.RESULTS_FORMAT](orch.results, output)
    logger.info('Saved intermediate results to file %s' % os.path.abspath(output))
    orch.stop()
    sys.exit(-signum)

def run(config, output):
    """ 
    Run function. It starts the simulator.
    experiments
    
    Parameters
    ----------
    config : str
        Path of the configuration file
    output : str
        The file name where results will be saved
    """
    # Read settings from file and save them in icarus.conf.settings
    settings = Settings()
    settings.read_from(config)
    # Config logger
    config_logging(settings.LOG_LEVEL)
    # set up orchestration
    orch = Orchestrator(settings)
    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP, signal.SIGQUIT):
        signal.signal(sig, functools.partial(handler, settings, orch, output))
    logger.info('Launching orchestrator')
    orch.run()
    logger.info('Orchestrator finished')
    results = orch.results
    results_writer_register[settings.RESULTS_FORMAT](results, output)
    logger.info('Saved results to file %s' % os.path.abspath(output))
    
def main():
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
    main(args.config, args.results)
    if args.plotsdir:
        plot.main(args.config, args.results, args.plotsdir)

if __name__ == '__main__':
    main()
