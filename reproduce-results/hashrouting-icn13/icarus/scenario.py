"""
This scripts generates the scenarios for running the simulation. It will
generate different topologies and event schedules and save them on as many XML
files.

This is completely detached from the main simulation. The main simulation
will read the topology and event schedule files and run the simulations
in the machine and save data on dedicated files
"""
from os import path
from random import choice, expovariate
from numpy import arange
import networkx as nx
import fnss
from icarus.util import ZipfDistribution
import icarus.config as config

###################### GENERAL CONFIGURATION PROPERTIES ######################
scenarios_dir = config.SCENARIOS_DIR
topo_prefix = config.TOPO_PREFIX
es_prefix = config.ES_PREFIX

# delays
# These values are suggested by this Computer Networks 2011 paper:
# http://www.cs.ucla.edu/classes/winter09/cs217/2011CN_NameRouting.pdf
# which is citing as source of this data, measurements from this IMC'06 paper:
# http://www.mpi-sws.org/~druschel/publications/ds2-imc.pdf
internal_link_delay = 2
external_link_delay = 3 * 34
##############################################################################

scenario_generator = {}

def register_scenario_generator(scenario_name):
    """Register a specific scenario generation function to the list of
    available scenario generators.
    
    The argument scenario_name is the name that identifies the scenario being
    generated
    """
    def _decorator(function):
        scenario_generator[scenario_name] = function
        return function
    return _decorator


def gen_req_schedule(receivers, rate, duration_warmup, duration_real, n_contents, alpha):
    """
    Generate schedule of requests
    
    Parameters
    ----------
    receivers : list
        List of receivers
    rate : float
        Rate of requests (per receiver)
    duration_warmup : float
        Length of warmup period (run without logging, for cache prepopulation)
    duration_real : float
        Length of measured period (run with logging)
    n_contents : int
        Size of content population
    alpha : float
        Alpha of Zipf content distribution
    """
    zipf = ZipfDistribution(alpha, n_contents)
    def event_generator(log):
        recv = choice(receivers)
        content = int(zipf.rand_val())
        return {'receiver': recv, 'content': content, 'log': log}
    es_warm = fnss.poisson_process_event_schedule(1.0/rate, 0, duration_warmup, 'ms', event_generator, False)
    es_real = fnss.poisson_process_event_schedule(1.0/rate, duration_warmup, duration_real, 'ms', event_generator, True)
    es_warm.add_schedule(es_real)
    return es_warm
    
    
def req_generator(topology, n_contents, alpha, rate=12.0, duration_warmup=9000, duration_real=36000):
    """This function generates events on the fly, i.e. instead of creating an 
    event schedule to be kept in memory, returns an iterator that generates
    events when needed.
    
    This is useful for running large schedules of events where RAM is limited
    as its memory impact is considerably lower.
    """
    rate = 12.0
    warmup = 9000
    duration = 36000
    
    receivers = [v for v in topology.nodes_iter() if topology.node[v]['stack'][0] == 'receiver']
    zipf = ZipfDistribution(alpha, n_contents)
    
    t_event = (expovariate(rate))
    while t_event < warmup + duration:
        recv = choice(receivers)
        content = int(zipf.rand_val())
        log = (t_event > warmup)
        event = {'receiver': recv, 'content': content, 'log': log}
        yield (t_event, event)
        t_event += (expovariate(rate))
    raise StopIteration()


@register_scenario_generator('GEANT')
def scenario_geant(net_cache=[0.05], n_contents=100000, alpha=[0.6, 0.8, 1.0]):
    """
    Return a scenario based on GARR topology
    
    Parameters
    ----------
    scenario_id : str
        String identifying the scenario (will be in the filename)
    net_cache : float
        Size of network cache (sum of all caches) normalized by size of content
        population
    n_contents : int
        Size of content population
    alpha : float
        List of alpha of Zipf content distribution
    """
    rate = 12.0
    warmup = 9000
    duration = 36000
    
    T = 'GEANT' # name of the topology
    # 240 nodes in the main component
    topology = fnss.parse_topology_zoo(path.join(scenarios_dir, 'resources/Geant2012.graphml')).to_undirected()
    topology = nx.connected_component_subgraphs(topology)[0]
    
    deg = nx.degree(topology)

    receivers = [v for v in topology.nodes() if deg[v] == 1] # 8 nodes
    
    caches = [v for v in topology.nodes() if deg[v] > 2] # 19 nodes
    
    # attach sources to topology
    source_attachments = [v for v in topology.nodes() if deg[v] == 2] # 13 nodes
    sources = []
    for v in source_attachments:
        u = v + 1000 # node ID of source
        topology.add_edge(v, u)
        sources.append(u)
    
    routers = [v for v in topology.nodes() if v not in caches + sources + receivers]
    
    # randomly allocate contents to sources
    contents = dict([(v, []) for v in sources])
    for c in range(1, n_contents + 1):
        s = choice(sources)
        contents[s].append(c)
    
    for v in sources:
        fnss.add_stack(topology, v, 'source', {'contents': contents[v]})
    for v in receivers:
        fnss.add_stack(topology, v, 'receiver', {})
    for v in routers:
        fnss.add_stack(topology, v, 'router', {})

    # set weights and delays on all links
    fnss.set_weights_constant(topology, 1.0)
    fnss.set_delays_constant(topology, internal_link_delay, 'ms')
    
    # label links as internal or external
    for u, v in topology.edges():
        if u in sources or v in sources:
            topology.edge[u][v]['type'] = 'external'
            # this prevents sources to be used to route traffic
            fnss.set_weights_constant(topology, 1000.0, [(u, v)])
            fnss.set_delays_constant(topology, external_link_delay, 'ms', [(u, v)])
        else:
            topology.edge[u][v]['type'] = 'internal'
            
            
    for nc in net_cache:
        size = (float(nc)*n_contents)/len(caches) # size of a single cache
        C = str(nc)
        for v in caches:
            fnss.add_stack(topology, v, 'cache', {'size': size})
        fnss.write_topology(topology, path.join(scenarios_dir, topo_prefix + 'T=%s@C=%s' % (T, C)  + '.xml'))
        print('[WROTE TOPOLOGY] T: %s, C: %s' % (T, C))
    
    for a in alpha:
        event_schedule = gen_req_schedule(receivers, rate, warmup, duration, n_contents, a)
        fnss.write_event_schedule(event_schedule, path.join(scenarios_dir, es_prefix + 'T=%s@A=%s' % (T, str(a)) + '.xml'))
        print('[WROTE SCHEDULE] T: %s, Alpha: %s, Events: %d' % (T, str(a), len(event_schedule)))


@register_scenario_generator('TISCALI')
def scenario_tiscali(net_cache=[0.05], n_contents=100000, alpha=[0.6, 0.8, 1.0]):
    """
    Return a scenario based on Tiscali topology, parsed from RocketFuel dataset
    
    Parameters
    ----------
    scenario_id : str
        String identifying the scenario (will be in the filename)
    net_cache : float
        Size of network cache (sum of all caches) normalized by size of content
        population
    n_contents : int
        Size of content population
    alpha : float
        List of alpha of Zipf content distribution
    """
    rate = 12.0
    warmup = 9000
    duration = 36000
    
    T = 'TISCALI' # name of the topology
    # 240 nodes in the main component
    topology = fnss.parse_rocketfuel_isp_map(path.join(scenarios_dir, 'resources/3257.r0.cch')).to_undirected()
    topology = nx.connected_component_subgraphs(topology)[0]
    
    deg = nx.degree(topology)
    onedeg = [v for v in topology.nodes() if deg[v] == 1] # they are 80
    
    # we select as caches nodes with highest degrees
    # we use as min degree 6 --> 36 nodes
    # If we changed min degrees, that would be the number of caches we would have:
    # Min degree    N caches
    #  2               160
    #  3               102
    #  4                75
    #  5                50
    #  6                36
    #  7                30
    #  8                26
    #  9                19
    # 10                16
    # 11                12
    # 12                11
    # 13                 7
    # 14                 3
    # 15                 3
    # 16                 2
    caches = [v for v in topology.nodes() if deg[v] >= 6] # 36 nodes
    
    # sources are node with degree 1 whose neighbor has degree at least equal to 5
    # we assume that sources are nodes connected to a hub
    # they are 44
    sources = [v for v in onedeg if deg[list(topology.edge[v].keys())[0]] > 4.5] # they are 

    # receivers are node with degree 1 whose neighbor has degree at most equal to 4
    # we assume that receivers are nodes not well connected to the network
    # they are 36   
    receivers = [v for v in onedeg if deg[list(topology.edge[v].keys())[0]] < 4.5]

    # we set router stacks because some strategies will fail if no stacks
    # are deployed 
    routers = [v for v in topology.nodes() if v not in caches + sources + receivers]

    # set weights and delays on all links
    fnss.set_weights_constant(topology, 1.0)
    fnss.set_delays_constant(topology, internal_link_delay, 'ms')

    # randomly allocate contents to sources
    contents = dict([(v, []) for v in sources])
    for c in range(1, n_contents + 1):
        s = choice(sources)
        contents[s].append(c)
    
    for v in sources:
        fnss.add_stack(topology, v, 'source', {'contents': contents[v]})
    for v in receivers:
        fnss.add_stack(topology, v, 'receiver', {})
    for v in routers:
        fnss.add_stack(topology, v, 'router', {})

    # label links as internal or external
    for u, v in topology.edges():
        if u in sources or v in sources:
            topology.edge[u][v]['type'] = 'external'
            # this prevents sources to be used to route traffic
            fnss.set_weights_constant(topology, 1000.0, [(u, v)])
            fnss.set_delays_constant(topology, external_link_delay, 'ms', [(u, v)])
        else:
            topology.edge[u][v]['type'] = 'internal'
            
            
    for nc in net_cache:
        size = (float(nc)*n_contents)/len(caches) # size of a single cache
        C = str(nc)
        for v in caches:
            fnss.add_stack(topology, v, 'cache', {'size': size})
        fnss.write_topology(topology, path.join(scenarios_dir, topo_prefix + 'T=%s@C=%s' % (T, C)  + '.xml'))
        print('[WROTE TOPOLOGY] T: %s, C: %s' % (T, C))
    
    for a in alpha:
        event_schedule = gen_req_schedule(receivers, rate, warmup, duration, n_contents, a)
        fnss.write_event_schedule(event_schedule, path.join(scenarios_dir, es_prefix + 'T=%s@A=%s' % (T, str(a)) + '.xml'))
        print('[WROTE SCHEDULE] T: %s, Alpha: %s, Events: %d' % (T, str(a), len(event_schedule)))


@register_scenario_generator('WIDE')
def scenario_wide(net_cache=[0.05], n_contents=100000, alpha=[0.6, 0.8, 1.0]):
    """
    Return a scenario based on GARR topology
    
    Parameters
    ----------
    scenario_id : str
        String identifying the scenario (will be in the filename)
    net_cache : float
        Size of network cache (sum of all caches) normalized by size of content
        population
    n_contents : int
        Size of content population
    alpha : float
        List of alpha of Zipf content distribution
    """
    rate = 12.0
    warmup = 9000
    duration = 36000
    
    T = 'WIDE' # name of the topology
    
    topology = fnss.parse_topology_zoo(path.join(scenarios_dir, 'resources/WideJpn.graphml')).to_undirected()
    # sources are nodes representing neighbouring AS's
    sources = [9, 8, 11, 13, 12, 15, 14, 17, 16, 19, 18]
    # receivers are internal nodes with degree = 1
    receivers = [27, 28, 3, 5, 4, 7]
    # caches are all remaining nodes --> 27 caches
    caches = [n for n in topology.nodes() if n not in receivers + sources]

    # set weights and delays on all links
    fnss.set_weights_constant(topology, 1.0)
    fnss.set_delays_constant(topology, internal_link_delay, 'ms')

    # randomly allocate contents to sources
    contents = dict([(v, []) for v in sources])
    for c in range(1, n_contents + 1):
        s = choice(sources)
        contents[s].append(c)
    
    for v in sources:
        fnss.add_stack(topology, v, 'source', {'contents': contents[v]})
    for v in receivers:
        fnss.add_stack(topology, v, 'receiver', {})
    
    # label links as internal or external
    for u, v in topology.edges():
        if u in sources or v in sources:
            topology.edge[u][v]['type'] = 'external'
            # this prevents sources to be used to route traffic
            fnss.set_weights_constant(topology, 1000.0, [(u, v)])
            fnss.set_delays_constant(topology, external_link_delay, 'ms',[(u, v)])
        else:
            topology.edge[u][v]['type'] = 'internal'
            
    for nc in net_cache:
        size = (float(nc)*n_contents)/len(caches) # size of a single cache
        C = str(nc)
        for v in caches:
            fnss.add_stack(topology, v, 'cache', {'size': size})
        fnss.write_topology(topology, path.join(scenarios_dir, topo_prefix + 'T=%s@C=%s' % (T, C)  + '.xml'))
        print('[WROTE TOPOLOGY] T: %s, C: %s' % (T, C))
            
    for a in alpha:
        event_schedule = gen_req_schedule(receivers, rate, warmup, duration, n_contents, a)
        fnss.write_event_schedule(event_schedule, path.join(scenarios_dir, es_prefix + 'T=%s@A=%s' % (T, str(a)) + '.xml'))
        print('[WROTE SCHEDULE] T: %s, Alpha: %s, Events: %d' % (T, str(a), len(event_schedule)))


@register_scenario_generator('GARR')
def scenario_garr(net_cache=[0.01, 0.05], n_contents=100000, alpha=[0.6, 0.8, 1.0]):
    """
    Return a scenario based on GARR topology
    
    Parameters
    ----------
    scenario_id : str
        String identifying the scenario (will be in the filename)
    net_cache : float
        Size of network cache (sum of all caches) normalized by size of content
        population
    n_contents : int
        Size of content population
    alpha : float
        List of alpha of Zipf content distribution
    """
    rate = 12.0
    warmup = 9000
    duration = 36000
    
    T = 'GARR' # name of the topology
    
    topology = fnss.parse_topology_zoo(path.join(scenarios_dir, 'resources/Garr201201.graphml')).to_undirected()
    # sources are nodes representing neighbouring AS's
    sources = [0, 2, 3, 5, 13, 16, 23, 24, 25, 27, 51, 52, 54]
    # receivers are internal nodes with degree = 1
    receivers = [1, 7, 8, 9, 11, 12, 19, 26, 28, 30, 32, 33, 41, 42, 43, 47, 48, 50, 53, 57, 60]
    # caches are all remaining nodes --> 27 caches
    caches = [n for n in topology.nodes() if n not in receivers + sources]

    # set weights and delays on all links
    fnss.set_weights_constant(topology, 1.0)
    fnss.set_delays_constant(topology, internal_link_delay, 'ms')

    # randomly allocate contents to sources
    contents = dict([(v, []) for v in sources])
    for c in range(1, n_contents + 1):
        s = choice(sources)
        contents[s].append(c)
    
    for v in sources:
        fnss.add_stack(topology, v, 'source', {'contents': contents[v]})
    for v in receivers:
        fnss.add_stack(topology, v, 'receiver', {})
    
    # label links as internal or external
    for u, v in topology.edges():
        if u in sources or v in sources:
            topology.edge[u][v]['type'] = 'external'
            # this prevents sources to be used to route traffic
            fnss.set_weights_constant(topology, 1000.0, [(u, v)])
            fnss.set_delays_constant(topology, external_link_delay, 'ms',[(u, v)])
        else:
            topology.edge[u][v]['type'] = 'internal'
    for nc in net_cache:
        size = (float(nc)*n_contents)/len(caches) # size of a single cache
        C = str(nc)
        for v in caches:
            fnss.add_stack(topology, v, 'cache', {'size': size})
        fnss.write_topology(topology, path.join(scenarios_dir, topo_prefix + 'T=%s@C=%s' % (T, C)  + '.xml'))
        print('[WROTE TOPOLOGY] T: %s, C: %s' % (T, C))
    for a in alpha:
        event_schedule = gen_req_schedule(receivers, rate, warmup, duration, n_contents, a)
        fnss.write_event_schedule(event_schedule, path.join(scenarios_dir, es_prefix + 'T=%s@A=%s' % (T, str(a)) + '.xml'))
        print('[WROTE SCHEDULE] T: %s, Alpha: %s, Events: %d' % (T, str(a), len(event_schedule)))


def main():
    # Generate all possible scenarios
    a = arange(0.6, 1.1, 0.1)
    c = [0.0004, 0.002, 0.01, 0.05]
    T = ['GEANT', 'WIDE', 'TISCALI', 'GARR']
    for t in T:
        scenario_generator[t](net_cache=c, n_contents=300000, alpha=a)


if __name__ == '__main__':
    main()
    

