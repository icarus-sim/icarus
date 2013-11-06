"""
This module contains all configuration information used to run simulations
"""
from os import path
from multiprocessing import cpu_count
from numpy import arange

# Directory config
LOG_DIR = path.abspath(path.join(path.dirname(__file__), path.pardir, 'logs'))
SCENARIOS_DIR = path.abspath(path.join(path.dirname(__file__), path.pardir, 'scenarios'))
GRAPHS_DIR = path.abspath(path.join(path.dirname(__file__), path.pardir, 'graphs'))

# Naming config
TOPO_PREFIX = 'TOPO_'
ES_PREFIX = 'ES_'

######################## PARAMETERS OF THE EXPERIMENTS ########################
ALPHA_RANGE = arange(0.6, 1.11, 0.1) # from 0.6 to 1.1 (included) with 0.1 steps
NET_CACHE_RANGE = [0.0004, 0.002, 0.01, 0.05]
TOPOLOGY_RANGE = ['GEANT', 'WIDE', 'TISCALI', 'GARR']

ALPHA_FIX = 0.8
NET_CACHE_FIX = 0.002
TOPOLOGY_FIX = 'GEANT'

N_CONTENTS = 300000

STRATEGIES = [
     'CEE+LRU',
     'HrSymm',
     'HrAsymm',
     'HrHybStr02',
     'HrHybSymMC',
     'CL4M',
     'ProbCache',
     'HrMCast',
     'NoCache',
             ]

# If True, generate new scenario files before running the simulation
GEN_SCENARIOS = True

# If True will write a dedicated log files per each scenario detailing every event
# This is useful if you want to plot time evolution of certain variables or to
# postprocess simulation results in ways you don't know at the time of running
# the simulation, but notice that for long simulations, files are likely to become
# extremely large
LOG_EVERYTHING = False

# add to the cache hit ratio summary file, analytical results of optimal cache hits
CALC_OPTIMAL_CACHE_HIT_RATIO = True

# if True events will be read from the event schedule file. If used in conjuction
# with generate_scenario = True, when a topology is created, an event schedule
# is created too.
# If False, events will be generated random on the fly. This minimizes RAM impact
# of events schedule creation.
USE_EVENTS_FILE = False

# If True, executes simulations in parallel
PARALLEL_EXEC = False
# Number of processes used to run simulations in parallel.
# This option is ignored if PARALLEL_EXEC == False
N_PROCESSES = cpu_count() - 1


