#!/usr/bin/env python
"""
This is a script to execute various simulation scenarios, possibly, in parallel

It orchestrates the whole execution of experiments and collection of logs.
"""
from os import path
from time import gmtime, strftime, sleep
from multiprocessing import Pool
from fnss import read_event_schedule, read_topology
import icarus.logging as logging
import icarus.config as config
from icarus.engine import run
from icarus.scenario import scenario_generator, req_generator

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
    run(topo, es, scenario_id, s) 


def main():
    """ 
    Main function, called from command line. It actually runs all the experiments
    """
    # Get all parameters from configuration file
    topologies = config.TOPOLOGIES
    use_events_file = config.USE_EVENTS_FILE
    n_contents = config.N_CONTENTS
    alpha = config.ALPHA
    net_cache = config.NET_CACHE
    strategies = config.STRATEGIES
    calc_optimal_cache_hit = config.CALC_OPTIMAL_CACHE_HIT_RATIO
    
    log_dir = config.LOG_DIR
    
    parallel_exec = config.PARALLEL_EXEC
    n_processes = config.N_PROCESSES
    
    if parallel_exec:
        pool = Pool(n_processes)
    
    # Generate scenarios before running simulation
    alpha_schedule = config.ALPHA if use_events_file else []
    if config.GEN_SCENARIOS:
        print ('[START SCENARIO GENERATION] Time: %s'
               % strftime("%H:%M:%S %Y-%m-%d", gmtime()))
        for t in topologies:
            scenario_generator[t](net_cache=net_cache, n_contents=n_contents, alpha=alpha_schedule)
        print ('[END SCENARIO GENERATION] Time: %s'
               % strftime("%H:%M:%S %Y-%m-%d", gmtime()))
    
    # Run actual simulations
    print ('[START ALL SIMULATIONS] Time: %s'
           % strftime("%H:%M:%S %Y-%m-%d", gmtime()))
    for t in topologies:
        for a in alpha:
            for c in net_cache:
                for s in strategies:
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
        logging.CacheHitRatioSummary(log_dir).append_optimal_cache_hit(topologies, alpha, net_cache, n_contents)
    
    print ('[END ALL SIMULATIONS] Time: %s'
           % strftime("%H:%M:%S %Y-%m-%d", gmtime()))


if __name__ == '__main__':
    main()