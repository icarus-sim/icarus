#!/usr/bin/env python
"""
This module implements the actual simulation engine
 
To launch the simulation, type:

python simrun.py topology.xml eventschedule.xml name_scenario
"""
from sys import argv, exit
from os import path, mkdir
from time import gmtime, strftime
from fnss import read_topology, read_event_schedule
import icarus.config as config
from icarus.strategy import strategy_impl


def run(topology, event_schedule, scenario_id, strategy_id, strategy_params=None):
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

    
def main():
    """Main function"""
    if len(argv) != 5:
        print('Usage: python simrun.py topology.xml eventschedule.xml name_scenario strategy')
        exit(1)
    # parse arguments
    topology = read_topology(argv[1])# parse from command line
    event_schedule = read_event_schedule(argv[2]) # parse from command line
    scenario_id = argv[3]
    strategy_id = argv[4]
    run(topology, event_schedule, scenario_id, strategy_id)
    

if __name__ == '__main__':
    main()
