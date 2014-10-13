#!/usr/bin/env python
"""Launches a simulation campaign and save results.
"""
import sys
import os
import signal
import functools
import logging

from icarus.util import Settings, config_logging
from icarus.registry import RESULTS_WRITER
from icarus.orchestration import Orchestrator


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
    RESULTS_WRITER[settings.RESULTS_FORMAT](orch.results, output)
    logger.info('Saved intermediate results to file %s' % os.path.abspath(output))
    orch.stop()
    sys.exit(-signum)

def run(config_file, output, config_override):
    """ 
    Run function. It starts the simulator.
    experiments
    
    Parameters
    ----------
    config : str
        Path of the configuration file
    output : str
        The file name where results will be saved
    config_override : dict, optional
        Configuration parameters overriding parameters in the file
    """
    # Read settings from file and save them in icarus.conf.settings
    settings = Settings()
    settings.read_from(config_file)
    if config_override:
        for k, v in config_override.iteritems():
            try:
                v = eval(v)
            except NameError:
                pass
            settings.set(k, v)
    settings.freeze()
    # Config logger
    config_logging(settings.LOG_LEVEL)
    # set up orchestration
    orch = Orchestrator(settings)
    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP, signal.SIGQUIT, signal.SIGABRT):
        signal.signal(sig, functools.partial(handler, settings, orch, output))
    logger.info('Launching orchestrator')
    orch.run()
    logger.info('Orchestrator finished')
    results = orch.results
    RESULTS_WRITER[settings.RESULTS_FORMAT](results, output)
    logger.info('Saved results to file %s' % os.path.abspath(output))
