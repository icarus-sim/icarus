"""This module contains all configuration information used to run simulations
"""
from multiprocessing import cpu_count
from collections import deque

# Level of logging output
# Available options: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL = 'INFO'

# Range of alpha values of the Zipf distribution using to generate content requests
# alpha values must be positive. The greater the value the more skewed is the 
# content popularity distribution
# Range of alpha values of the Zipf distribution using to generate content requests
# alpha values must be positive. The greater the value the more skewed is the 
# content popularity distribution
# Note: to generate these alpha values, numpy.arange could also be used, but it
# is not recommended because generated numbers may be not those desired. 
# E.g. arange may return 0.799999999999 instead of 0.8. 
# This would give problems while trying to plot the results because if for
# example I wanted to filter experiment with alpha=0.8, experiments with
# alpha = 0.799999999999 would not be recognized 
ALPHA = [0.6, 0.7, 0.8, 0.9, 1.0, 1.1]

# Total size of network cache as a fraction of content population
NETWORK_CACHE = [0.004, 0.002, 0.01, 0.05]

# Number of content objects
N_CONTENTS = 3*10**5

# Granularity of caching.
# Currently, only OBJECT is supported
CACHING_GRANULARITY = 'OBJECT'

# Number of requests per second (over the whole network)
NETWORK_REQUEST_RATE = 12.0

# Number of content requests generated to prepopulate the caches
# These requests are not logged
N_WARMUP_REQUESTS = 2*10**5

# Number of content requests generated after the warmup and logged
# to generate results. 
N_MEASURED_REQUESTS = 5*10**5

# If True, executes simulations in parallel using multiple processes
# to take advantage of multicore CPUs
PARALLEL_EXECUTION = True

# Number of processes used to run simulations in parallel.
# This option is ignored if PARALLEL_EXECUTION = False
N_PROCESSES = cpu_count()

# Topologies used for the simulation.
# Topology implementations are located in ./icarus/scenarios/topology.py
TOPOLOGIES = ['GEANT', 'WIDE', 'GARR', 'TISCALI']

# Format in which results are saved.
# Result readers and writers are located in module ./icarus/results/readwrite.py
# Currently only PICKLE is supported 
RESULTS_FORMAT = 'PICKLE'

# List of caching and routing strategies tested
# This below is the complete list of strategies currently implemented.
# The code is located in ./icarus/models/strategy.py
STRATEGIES = [
     'LCE',             # Leave Copy Everywhere
     'NO_CACHE',        # No caching, shorest-path routing
     'HR_SYMM',         # Symmetric hash-routing
     'HR_ASYMM',        # Asymmetric hash-routing
     'HR_MULTICAST',    # Multicast hash-routing
     'HR_HYBRID_AM',    # Hybrid Asymm-Multicast hash-routing
     'HR_HYBRID_SM',    # Hybrid Symm-Multicast hash-routing
     'CL4M',            # Cache less for more
     'PROB_CACHE',      # ProbCache
     'LCD',             # Leave Copy Down
     'RAND_CHOICE',     # Random choice: cache in one random cache on path
     'RAND_BERNOULLI',  # Random Bernoulli: cache randomly in caches on path
             ]

# Cache replacement policy used by the network caches.
# Supported policies are: 'LRU', 'LFU', 'FIFO', 'RAND' and 'NULL'
# Cache policy implmentations are located in ./icarus/models/cache.py
CACHE_POLICY = 'LRU'

# Number of times each experiment is replicated
# This is necessary for extracting confidence interval of selected metrics
N_REPLICATIONS = 5

# List of metrics to be measured in the experiments
# The implementation of data collectors are located in ./icaurs/execution/collectors.py
DATA_COLLECTORS = ['CACHE_HIT_RATIO', 'LATENCY', 'LINK_LOAD', 'PATH_STRETCH']

# Queue of experiments
# To specify what experiment parameters to test, I can set set different values
# of NETWORK_CACHE, TOPOLOGIES, ALPHA, STRATEGIES and so on. The simulator will
# created experiment definition for all possible combinations of values and run
# the experiments. This approach may possibly lead to a very high number of 
# experiments.
# To prevent this issue, Icarus allows user to specify their own combination
# of experiments to run by setting this EXPERIMENT_QUEUE parameter. The
# EXPERIMENT_QUEUE setting must be an iterable container whereby each element
# is a dictionary of experiment attributes as shown in the example below.
# EXPERIMENT_QUEUE is optional. If it is set and it is not None, the settings
# ALPHA, NETWORK_CACHE, TOPOLOGIES and STRATEGIES will be ignored.
# 
# To use EXPERIMENT_QUEUE you can uncomment the code below or write your own
# implementation
#
EXPERIMENT_QUEUE = None
#EXPERIMENT_QUEUE = deque()
#for strategy_name in STRATEGIES:
#    for topology_name in TOPOLOGIES:
#        network_cache = 0.002
#        alpha = 0.8
#        params = dict(alpha=alpha, topology_name=topology_name,
#                      network_cache=network_cache, strategy_name=strategy_name,
#                      n_contents=N_CONTENTS, strategy_params={})
#        EXPERIMENT_QUEUE.append(params)
#    for alpha in ALPHA:
#        topology_name = 'GEANT'
#        network_cache = 0.002
#        params = dict(alpha=alpha, topology_name=topology_name,
#                      network_cache=network_cache, strategy_name=strategy_name,
#                      n_contents=N_CONTENTS, strategy_params={})    
#        EXPERIMENT_QUEUE.append(params)
#    for network_cache in NETWORK_CACHE:
#        for topology_name in TOPOLOGIES:
#            topology_name = 'GEANT'
#            alpha = 0.8
#            params = dict(alpha=alpha, topology_name=topology_name,
#                      network_cache=network_cache, strategy_name=strategy_name,
#                      n_contents=N_CONTENTS, strategy_params={})    
#        EXPERIMENT_QUEUE.append(params)

