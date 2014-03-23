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

from icarus.execution import exec_experiment
from icarus.scenarios import uniform_req_gen
from icarus.registry import topology_factory_register, cache_policy_register, \
                           strategy_register, data_collector_register
from icarus.results import ResultSet
from icarus.util import timestr


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
        # Calc number of experiments nad number of processes
        self.n_exp = len(queue) * self.settings.N_REPLICATIONS 
        self.n_proc = self.settings.N_PROCESSES \
                      if self.settings.PARALLEL_EXECUTION \
                      else 1
        logger.info('Starting simulations: %d experiments, %d process(es)' 
                    % (self.n_exp, self.n_proc))
        # Schedule experiments from the queue
        while queue:
            experiment = queue.popleft()
            for _ in range(self.settings.N_REPLICATIONS):
                if self.settings.PARALLEL_EXECUTION:
                    last_job = self.pool.apply_async(run_scenario,
                            args=(self.settings, experiment,
                                  self.seq.assign(), self.n_exp),
                            callback=self.experiment_callback)
                else:
                    self.experiment_callback(run_scenario(self.settings, 
                                    experiment, self.seq.assign(),
                                    self.n_exp))
                if self._stop:
                    self.stop()
                                
        # If parallel execution, wait for all processes to terminate
        if self.settings.PARALLEL_EXECUTION:
            self.pool.close()
            # This solution is not optimal, but at least makes KeyboardInterrupt
            # work fine, which is crucial if launching the simulation remotely
            # via screen.
            # What happens here is that we keep waiting for possible
            # KeyboardInterrupts till the last scheduled process terminates
            # successfully. The last scheduled process is not necessarily the last
            # finishing one but nothing bad is going to happen in such case, it
            # will only not be possible interrupting the simulation between the
            # last scheduled process ends and the last ending process ends, which
            # is likely a matter of seconds.
            try:
                while not last_job.ready(): time.sleep(5)
            except KeyboardInterrupt:
                self.pool.terminate()
                self.pool.join()
                return
            self.pool.join()
    
    
    def experiment_callback(self, args):
        """Callback method called by run_scenario
        
        Parameters
        ----------
        args : tuple
            Tuple of arguments
        """
        # Extract parameters
        params, results, seq, duration = args
        # Store results
        self.results.add((params, results))
        self.exp_durations.append(duration)
        if seq % self.summary_freq == 0:
            # Number of experiments scheduled to be executed
            n_scheduled = self.n_exp - seq
            # Compute ETA
            n_cores = min(mp.cpu_count(), self.n_proc)
            mean_duration = sum(self.exp_durations)/len(self.exp_durations)
            eta = timestr(n_scheduled*mean_duration/n_cores, False)
            # Print summary
            logger.info('SUMMARY | Completed: %d, Scheduled: %d, ETA: %s', 
                        seq, n_scheduled, eta)
        

class SequenceNumber(object):
    """This class models an increasing sequence number.
    
    It is used to assign a sequence number for an experiment in a thread-safe
    manner.
    """
    
    def __init__(self, initval=1):
        """Constructor
        
        Parameters
        ----------
        initval :int, optional
            The starting sequence number
        """
        self.__seq = initval - 1
        
    def assign(self):
        """Assigns a new sequence number.
        
        Returns
        -------
        seq : int
            The sequence number
        """
        self.__seq += 1
        seq = self.__seq
        return seq
    
    def current(self):
        """Return the latest sequence number assigned
        
        Returns
        -------
        seq : int
            The latest assigned sequence number
        """
        return self.__seq


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
    results : 2-tuple
        A 2-tuple of dictionaries. The first dict stores all the attributes of
        the experiment. The second dict stores the results.
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
        
        # Get topology and event generator
        topology = topology_factory_register[topology_name](network_cache, n_contents)   
        events = uniform_req_gen(topology, n_contents, alpha, 
                                          rate=settings.NETWORK_REQUEST_RATE,
                                          n_warmup=settings.N_WARMUP_REQUESTS,
                                          n_measured=settings.N_MEASURED_REQUESTS)
        topology.graph['cache_policy'] = cache_policy
    
        collectors = [(m, {}) for m in metrics]
        strategy = (strategy_name, strategy_params)
        logger.info('Experiment %d/%d | Start simulation', curr_exp, n_exp)
        results = exec_experiment(topology, events, strategy, collectors)
        duration = time.time() - start_time
        logger.info('Experiment %d/%d | End simulation | Duration %s.', 
                    curr_exp, n_exp, timestr(duration, True))
        return (params, results, curr_exp, duration)
    except KeyboardInterrupt:
        logger.error('Received keyboard interrupt. Terminating')
        sys.exit(-signal.SIGINT)
