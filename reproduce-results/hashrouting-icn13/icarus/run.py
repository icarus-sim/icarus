#!/usr/bin/env python
"""
This is a script to execute various simulation scenarios, possibly, in parallel

It orchestrates the whole execution of experiments and collection of logs.
"""
from os import path, mkdir
from sys import exit
from time import gmtime, strftime, sleep
from multiprocessing import Pool
from collections import deque
from fnss import read_event_schedule, read_topology
import icarus.logging as logging
import icarus.config as config
from icarus.scenario import scenario_generator, req_generator
from icarus.strategy import strategy_impl


def exec_experiment(topology, event_schedule, scenario_id, strategy_id, strategy_params=None):
    """
    Run the simulation of a specific scenario
    """
    if strategy_id not in strategy_impl:
        print('[ERROR] Strategy not recognized')
        exit(-1)
    # set up directory for logs
    log_dir = config.LOG_DIR
    if not path.exists(log_dir):
        mkdir(log_dir)
    strategy = strategy_impl[strategy_id](topology, log_dir, scenario_id, strategy_params)
    print('[%s][START SIMULATION] Scenario: %s' % (strftime("%H:%M:%S %Y-%m-%d", gmtime()), scenario_id))
    # run simulation
    for time, event in event_schedule:
        strategy.handle_event(time, event)
    # Closes all log files
    strategy.close()
    print('[%s][END SIMULATION] Scenario: %s' % (strftime("%H:%M:%S %Y-%m-%d", gmtime()), scenario_id))


def run_simulation_scenario(t, a, c, s):
    """Run a single simulation scenario with given topology, alpha, cache size
    and strategy
    """
    use_events_file = config.USE_EVENTS_FILE
    n_contents = config.N_CONTENTS
    scenarios_dir = config.SCENARIOS_DIR
    topo_prefix = config.TOPO_PREFIX
    es_prefix = config.ES_PREFIX
    
    topo_file = path.join(scenarios_dir, topo_prefix + 'T=%s@C=%s.xml' % (t, str(c)))
    scenario_id = 'T=%s@C=%s@A=%s@S=%s' % (t, str(c), str(a), s)
    topo = read_topology(topo_file)
    if use_events_file:
        es_file = path.join(scenarios_dir, es_prefix + 'T=%s@A=%s.xml' % (t, str(a)))
        es = read_event_schedule(es_file)
    else:
        es = req_generator(topo, n_contents, a)
    exec_experiment(topo, es, scenario_id, s) 


def main():
    """ 
    Main function, called from command line. It actually runs all the experiments
    """
    # Get all parameters from configuration file
    topology_range = config.TOPOLOGY_RANGE
    alpha_range = config.ALPHA_RANGE
    net_cache_range = config.NET_CACHE_RANGE
    topology_fix = config.TOPOLOGY_FIX
    alpha_fix = config.ALPHA_FIX
    net_cache_fix = config.NET_CACHE_FIX    
    strategies = config.STRATEGIES
    use_events_file = config.USE_EVENTS_FILE
    n_contents = config.N_CONTENTS
    calc_optimal_cache_hit = config.CALC_OPTIMAL_CACHE_HIT_RATIO
    
    log_dir = config.LOG_DIR
    
    parallel_exec = config.PARALLEL_EXEC
    n_processes = config.N_PROCESSES
    
    if parallel_exec:
        pool = Pool(n_processes)
    
    # Generate scenarios before running simulation
    alpha_schedule = config.ALPHA_RANGE if use_events_file else []
    if config.GEN_SCENARIOS:
        print ('[START SCENARIO GENERATION] Time: %s'
               % strftime("%H:%M:%S %Y-%m-%d", gmtime()))
        for t in topology_range:
            scenario_generator[t](net_cache=net_cache_range, n_contents=n_contents, alpha=alpha_schedule)
        print ('[END SCENARIO GENERATION] Time: %s'
               % strftime("%H:%M:%S %Y-%m-%d", gmtime()))
    
    # Run actual simulations
    print ('[START ALL SIMULATIONS] Time: %s'
           % strftime("%H:%M:%S %Y-%m-%d", gmtime()))
    params = deque()
    for t in topology_range:
        for s in strategies:
            params.append((t, alpha_fix, net_cache_fix, s))
    for c in net_cache_range:
        for s in strategies:
            params.append((topology_fix, alpha_fix, c, s))
    for a in alpha_range:
        for s in strategies:
            params.append((topology_fix, a, net_cache_fix, s))
    print ('[SUMMARY] The simulations comprise %d experiments' % len(params))  
    for t, a, c, s in params:
        if parallel_exec:
            last_job = pool.apply_async(run_simulation_scenario, args=(t, a, c, s))
        else:
            run_simulation_scenario(t, a, c, s)

    # If parallel execution, wait for all processes to terminate
    if parallel_exec:
        pool.close()
        # This solution is not optimal, but at least makes KeyboardInterrupt
        # work fine, which is crucial if launching the simulation remotely
        # via screen.
        # What happens here is that we keep waiting for possible
        #KeyboardInterrupts till the last scheduled process terminates
        # successfully. The last scheduled process is not necessarily the last
        # finishing one but nothing bad is going to happen in such case, it
        # will only not be possible interrupting the simulation between the
        # last scheduled process ends and the last ending process ends, which
        # is is a matter of seconds.  
        try:
            while not last_job.ready(): sleep(5)
        except KeyboardInterrupt:
            print "Caught KeyboardInterrupt, terminating workers"
            pool.terminate()
            pool.join()
            return
        pool.join()

    if calc_optimal_cache_hit:
        logging.CacheHitRatioSummary(log_dir).append_optimal_cache_hit(topology_range, alpha_range, net_cache_range, n_contents)
    
    print ('[END ALL SIMULATIONS] Time: %s'
           % strftime("%H:%M:%S %Y-%m-%d", gmtime()))


if __name__ == '__main__':
    main()