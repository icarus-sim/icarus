"""Orchestrate the execution of all experiments.

The orchestrator is responsible for scheduling experiments specified in the
user-provided settings.
"""
from __future__ import division
import time
import collections
import multiprocessing as mp
import logging
import copy
import sys
import signal
import traceback

from icarus.execution import exec_experiment
from icarus.registry import TOPOLOGY_FACTORY, CACHE_PLACEMENT, CONTENT_PLACEMENT, \
                            CACHE_POLICY, WORKLOAD, DATA_COLLECTOR, STRATEGY
from icarus.results import ResultSet
from icarus.util import SequenceNumber, timestr


__all__ = ['Orchestrator', 'run_scenario']


logger = logging.getLogger('orchestration')


class Orchestrator(object):
    """Orchestrator.

    It is responsible for orchestrating the execution of all experiments and
    aggregate results.
    """

    def __init__(self, settings, summary_freq=4):
        """Constructor

        Parameters
        ----------
        settings : Settings
            The settings of the simulator
        summary_freq : int
            Frequency (in number of experiment) at which summary messages
            are displayed
        """
        self.settings = settings
        self.results = ResultSet()
        self.seq = SequenceNumber()
        self.exp_durations = collections.deque(maxlen=30)
        self.n_success = 0
        self.n_fail = 0
        self.summary_freq = summary_freq
        self._stop = False
        if self.settings.PARALLEL_EXECUTION:
            self.pool = mp.Pool(settings.N_PROCESSES)

    def stop(self):
        """Stop the execution of the orchestrator
        """
        logger.info('Orchestrator is stopping')
        self._stop = True
        if self.settings.PARALLEL_EXECUTION:
            self.pool.terminate()
            self.pool.join()

    def run(self):
        """Run the orchestrator.

        This call is blocking, whether multiple processes are used or not. This
        methods returns only after all experiments are executed.
        """
        # Create queue of experiment configurations
        queue = collections.deque(self.settings.EXPERIMENT_QUEUE)
        # Calculate number of experiments and number of processes
        self.n_exp = len(queue) * self.settings.N_REPLICATIONS
        self.n_proc = self.settings.N_PROCESSES \
                      if self.settings.PARALLEL_EXECUTION \
                      else 1
        logger.info('Starting simulations: %d experiments, %d process(es)'
                    % (self.n_exp, self.n_proc))

        if self.settings.PARALLEL_EXECUTION:
            # Starting from Python 3.2, multiprocessing.Pool.apply_async
            # accepts a new error_callback argument that is a callable for
            # returning a message when uncaught errors are thrown.
            # The following lines ensure compatibility with Python < 3.2
            callbacks = {"callback": self.experiment_callback}
            if sys.version_info > (3, 2):
                callbacks["error_callback"] = self.error_callback
            # This job queue is used only to keep track of which jobs have
            # finished and which are still running. Currently this information
            # is used only to handle keyboard interrupts correctly
            job_queue = collections.deque()
            # Schedule experiments from the queue
            while queue:
                experiment = queue.popleft()
                for _ in range(self.settings.N_REPLICATIONS):
                    job_queue.append(self.pool.apply_async(run_scenario,
                            args=(self.settings, experiment,
                                  self.seq.assign(), self.n_exp),
                            **callbacks))
            self.pool.close()
            # This solution is probably not optimal, but at least makes
            # KeyboardInterrupt work fine, which is crucial if launching the
            # simulation remotely via screen.
            # What happens here is that we keep waiting for possible
            # KeyboardInterrupts till the last process terminates successfully.
            # We may have to wait up to 5 seconds after the last process
            # terminates before exiting, which is really negligible
            try:
                while job_queue:
                    job = job_queue.popleft()
                    while not job.ready():
                        time.sleep(5)
            except KeyboardInterrupt:
                self.pool.terminate()
            self.pool.join()

        else:  # Single-process execution
            while queue:
                experiment = queue.popleft()
                for _ in range(self.settings.N_REPLICATIONS):
                    self.experiment_callback(run_scenario(self.settings,
                                            experiment, self.seq.assign(),
                                            self.n_exp))
                    if self._stop:
                        self.stop()

        logger.info('END | Planned: %d, Completed: %d, Succeeded: %d, Failed: %d',
                    self.n_exp, self.n_fail + self.n_success, self.n_success, self.n_fail)

    def error_callback(self, msg):
        """Callback method called in case of error in Python > 3.2

        Parameters
        ----------
        msg : string
            Error message
        """
        logger.error("FAILURE | Experiment failed: {}".format(msg))
        self.n_fail += 1

    def experiment_callback(self, args):
        """Callback method called by run_scenario

        Parameters
        ----------
        args : tuple
            Tuple of arguments
        """
        # If args is None, that means that an exception was raised during the
        # execution of the experiment. In such case, ignore it
        if not args:
            self.n_fail += 1
            return
        # Extract parameters
        params, results, duration = args
        self.n_success += 1
        # Store results
        self.results.add(params, results)
        self.exp_durations.append(duration)
        if self.n_success % self.summary_freq == 0:
            # Number of experiments scheduled to be executed
            n_scheduled = self.n_exp - (self.n_fail + self.n_success)
            # Compute ETA
            n_cores = min(mp.cpu_count(), self.n_proc)
            mean_duration = sum(self.exp_durations) / len(self.exp_durations)
            eta = timestr(n_scheduled * mean_duration / n_cores, False)
            # Print summary
            logger.info('SUMMARY | Completed: %d, Failed: %d, Scheduled: %d, ETA: %s',
                        self.n_success, self.n_fail, n_scheduled, eta)


def run_scenario(settings, params, curr_exp, n_exp):
    """Run a single scenario experiment

    Parameters
    ----------
    settings : Settings
        The simulator settings
    params : Tree
        experiment parameters tree
    curr_exp : int
        sequence number of the experiment
    n_exp : int
        Number of scheduled experiments

    Returns
    -------
    results : 3-tuple
        A (params, results, duration) 3-tuple. The first element is a dictionary
        which stores all the attributes of the experiment. The second element
        is a dictionary which stores the results. The third element is an
        integer expressing the wall-clock duration of the experiment (in
        seconds)
    """
    try:
        start_time = time.time()
        proc_name = mp.current_process().name
        logger = logging.getLogger('runner-%s' % proc_name)

        # Get list of metrics required
        metrics = settings.DATA_COLLECTORS

        # Copy parameters so that they can be manipulated
        tree = copy.deepcopy(params)

        # Set topology
        topology_spec = tree['topology']
        topology_name = topology_spec.pop('name')
        if topology_name not in TOPOLOGY_FACTORY:
            logger.error('No topology factory implementation for %s was found.'
                         % topology_name)
            return None
        topology = TOPOLOGY_FACTORY[topology_name](**topology_spec)

        workload_spec = tree['workload']
        workload_name = workload_spec.pop('name')
        if workload_name not in WORKLOAD:
            logger.error('No workload implementation named %s was found.'
                         % workload_name)
            return None
        workload = WORKLOAD[workload_name](topology, **workload_spec)

        # Assign caches to nodes
        if 'cache_placement' in tree:
            cachepl_spec = tree['cache_placement']
            cachepl_name = cachepl_spec.pop('name')
            if cachepl_name not in CACHE_PLACEMENT:
                logger.error('No cache placement named %s was found.'
                             % cachepl_name)
                return None
            network_cache = cachepl_spec.pop('network_cache')
            # Cache budget is the cumulative number of cache entries across
            # the whole network
            cachepl_spec['cache_budget'] = workload.n_contents * network_cache
            CACHE_PLACEMENT[cachepl_name](topology, **cachepl_spec)

        # Assign contents to sources
        # If there are many contents, after doing this, performing operations
        # requiring a topology deep copy, i.e. to_directed/undirected, will
        # take long.
        contpl_spec = tree['content_placement']
        contpl_name = contpl_spec.pop('name')
        if contpl_name not in CONTENT_PLACEMENT:
            logger.error('No content placement implementation named %s was found.'
                         % contpl_name)
            return None
        CONTENT_PLACEMENT[contpl_name](topology, workload.contents, **contpl_spec)

        # caching and routing strategy definition
        strategy = tree['strategy']
        if strategy['name'] not in STRATEGY:
            logger.error('No implementation of strategy %s was found.' % strategy['name'])
            return None

        # cache eviction policy definition
        cache_policy = tree['cache_policy']
        if cache_policy['name'] not in CACHE_POLICY:
            logger.error('No implementation of cache policy %s was found.' % cache_policy['name'])
            return None

        # Configuration parameters of network model
        netconf = tree['netconf']

        # Text description of the scenario run to print on screen
        scenario = tree['desc'] if 'desc' in tree else "Description N/A"

        logger.info('Experiment %d/%d | Preparing scenario: %s', curr_exp, n_exp, scenario)

        if any(m not in DATA_COLLECTOR for m in metrics):
            logger.error('There are no implementations for at least one data collector specified')
            return None

        collectors = {m: {} for m in metrics}

        logger.info('Experiment %d/%d | Start simulation', curr_exp, n_exp)
        results = exec_experiment(topology, workload, netconf, strategy, cache_policy, collectors)

        duration = time.time() - start_time
        logger.info('Experiment %d/%d | End simulation | Duration %s.',
                    curr_exp, n_exp, timestr(duration, True))
        return (params, results, duration)
    except KeyboardInterrupt:
        logger.error('Received keyboard interrupt. Terminating')
        sys.exit(-signal.SIGINT)
    except Exception as e:
        err_type = str(type(e)).split("'")[1].split(".")[1]
        err_message = e.message
        logger.error('Experiment %d/%d | Failed | %s: %s\n%s',
                     curr_exp, n_exp, err_type, err_message,
                     traceback.format_exc())
