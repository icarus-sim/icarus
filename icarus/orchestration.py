"""Contains the code that orchestrates the execution of all experiments.

The orchestrator is responsible for designing experiments with all combinations
of parameters specified in the user-provided settings, schedule experiment
execution on various
"""
from __future__ import division
import time
import collections
import multiprocessing as mp
import logging
import sys
import signal
import traceback

from icarus.execution import exec_experiment
from icarus.scenarios import uniform_req_gen
from icarus.registry import topology_factory_register, cache_policy_register, \
                           strategy_register, data_collector_register
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
        if settings.PARALLEL_EXECUTION:
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
        if 'EXPERIMENT_QUEUE' in self.settings and self.settings.EXPERIMENT_QUEUE:
            queue = collections.deque(self.settings.EXPERIMENT_QUEUE)
        else:
            queue = collections.deque()
            n_contents = self.settings.N_CONTENTS
            for topology_name in self.settings.TOPOLOGIES:
                for network_cache in self.settings.NETWORK_CACHE:
                    for alpha in self.settings.ALPHA:
                        for strategy_name in self.settings.STRATEGIES:
                            params = dict(alpha=alpha,
                                          topology_name=topology_name,
                                          network_cache=network_cache,
                                          strategy_name=strategy_name,
                                          n_contents=n_contents,
                                          strategy_params={})
                            queue.append(params)
        # Calculate number of experiments and number of processes
        self.n_exp = len(queue) * self.settings.N_REPLICATIONS 
        self.n_proc = self.settings.N_PROCESSES \
                      if self.settings.PARALLEL_EXECUTION \
                      else 1
        logger.info('Starting simulations: %d experiments, %d process(es)' 
                    % (self.n_exp, self.n_proc))
        
        if self.settings.PARALLEL_EXECUTION:
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
                            callback=self.experiment_callback))
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
        
        else: # Single-process execution
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
            mean_duration = sum(self.exp_durations)/len(self.exp_durations)
            eta = timestr(n_scheduled*mean_duration/n_cores, False)
            # Print summary
            logger.info('SUMMARY | Completed: %d, Failed: %d, Scheduled: %d, ETA: %s', 
                        self.n_success, self.n_fail, n_scheduled, eta)
        

def run_scenario(settings, params, curr_exp, n_exp):
    """Run a single scenario experiment
    
    Parameters
    ----------
    settings : Settings
        The simulator settings
    params : dict
        Dictionary of parameters
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
    
        alpha = params['alpha']
        topology_name = params['topology_name']
        network_cache = params['network_cache']
        strategy_name = params['strategy_name']
        n_contents = params['n_contents']
        strategy_params = params['strategy_params']
        cache_policy = params['cache_policy'] if 'cache_policy' in params \
                       and params['cache_policy'] is not None \
                       else settings.CACHE_POLICY
        metrics = settings.DATA_COLLECTORS
        
        scenario = "%s, %s, alpha: %s, netcache: %s" % (topology_name, strategy_name, str(alpha), str(network_cache))
        logger.info('Experiment %d/%d | Preparing scenario: %s', curr_exp, n_exp, scenario)
        
        # Check parameters
        if topology_name not in topology_factory_register:
            logger.error('No topology factory implementation for %s was found.' % topology_name)
            return None
        if cache_policy not in cache_policy_register:
            logger.error('No implementation of cache policy %s was found.' % cache_policy)
            return None
        if strategy_name not in strategy_register:
            logger.error('No implementation of strategy %s was found.' % strategy_name)
            return None
        if any(m not in data_collector_register for m in metrics):
            logger.error('There are no implementations for at least one data collector specified')
            return None
        # Get user-defined seed, if any
        seed = settings.SEED if 'SEED' in settings else None
        # Get topology and event generator
        topology = topology_factory_register[topology_name](network_cache, n_contents, seed=seed)   
        events = uniform_req_gen(topology, n_contents, alpha, 
                                          rate=settings.NETWORK_REQUEST_RATE,
                                          n_warmup=settings.N_WARMUP_REQUESTS,
                                          n_measured=settings.N_MEASURED_REQUESTS,
                                          seed=seed)
        topology.graph['cache_policy'] = cache_policy
    
        collectors = [(m, {}) for m in metrics]
        strategy = (strategy_name, strategy_params)
        logger.info('Experiment %d/%d | Start simulation', curr_exp, n_exp)
        results = exec_experiment(topology, events, strategy, collectors)
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
