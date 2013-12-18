"""This module contains functions for creating or importing topologies for the
experiments.
"""
from os import path

import networkx as nx
import fnss

from icarus.scenarios import uniform_cache_placement, uniform_content_placement
from icarus.registry import register_topology_factory


__all__ = [
        'topology_binary_tree',
        'topology_path',
        'topology_geant',
        'topology_tiscali',
        'topology_wide',
        'topology_garr',
           ]


# Delays
# These values are suggested by this Computer Networks 2011 paper:
# http://www.cs.ucla.edu/classes/winter09/cs217/2011CN_NameRouting.pdf
# which is citing as source of this data, measurements from this IMC'06 paper:
# http://www.mpi-sws.org/~druschel/publications/ds2-imc.pdf
INTERNAL_LINK_DELAY = 2
EXTERNAL_LINK_DELAY = 3 * 34


TOPOLOGY_RESOURCES_DIR = path.abspath(path.join(path.dirname(__file__), 
                                                path.pardir, path.pardir, 
                                                'resources', 'topologies'))


@register_topology_factory('BINARY_TREE')
def topology_binary_tree(network_cache=0.05, n_contents=100000, seed=None):
    """
    Returns a tree topology
    Parameters
    ----------
    network_cache : float
        Size of network cache (sum of all caches) normalized by size of content
        population
    n_contents : int
        Size of content population
    seed : int, optional
        The seed used for random number generation
        
    Returns
    -------
    topology : fnss.Topology
        The topology object
    """
    h = 5       # depth of the tree
    topology = fnss.k_ary_tree_topology(2, h)
    receivers = [v for v in topology.nodes_iter()
                 if topology.node[v]['depth'] == h]
    sources = [v for v in topology.nodes_iter()
               if topology.node[v]['depth'] == 0]
    caches = [v for v in topology.nodes_iter()
              if topology.node[v]['depth'] > 0
              and topology.node[v]['depth'] < h]
    # randomly allocate contents to sources
    content_placement = uniform_content_placement(topology, range(1, n_contents+1), sources, seed=seed)
    for v in sources:
        fnss.add_stack(topology, v, 'source', {'contents': content_placement[v]})
    for v in receivers:
        fnss.add_stack(topology, v, 'receiver', {})
    cache_placement = uniform_cache_placement(topology, network_cache*n_contents, caches)
    for node, size in cache_placement.iteritems():
        fnss.add_stack(topology, node, 'cache', {'size': size})
    # set weights and delays on all links
    fnss.set_weights_constant(topology, 1.0)
    fnss.set_delays_constant(topology, INTERNAL_LINK_DELAY, 'ms')
    # label links as internal or external
    for u, v in topology.edges_iter():
        if u in sources or v in sources:
            topology.edge[u][v]['type'] = 'external'
            fnss.set_delays_constant(topology, EXTERNAL_LINK_DELAY, 'ms', [(u, v)])
        else:
            topology.edge[u][v]['type'] = 'internal'
    return topology


@register_topology_factory('PATH')
def topology_path(network_cache=0.05, n_contents=100000, n=3, seed=None):
    """
    Return a scenario based on path topology
    
    Parameters
    ----------
    network_cache : float
        Size of network cache (sum of all caches) normalized by size of content
        population
    n_contents : int
        Size of content population
    seed : int, optional
        The seed used for random number generation
        
    Returns
    -------
    topology : fnss.Topology
        The topology object
    """
    # 240 nodes in the main component
    topology = fnss.line_topology(n)
    receivers = [0]    
    caches = range(1, n-1)
    sources = [n-1]
    # randomly allocate contents to sources
    content_placement = uniform_content_placement(topology, range(1, n_contents+1), sources, seed=seed)
    for v in sources:
        fnss.add_stack(topology, v, 'source', {'contents': content_placement[v]})
    for v in receivers:
        fnss.add_stack(topology, v, 'receiver', {})
    # set weights and delays on all links
    fnss.set_weights_constant(topology, 1.0)
    fnss.set_delays_constant(topology, INTERNAL_LINK_DELAY, 'ms')
    # label links as internal or external
    for u, v in topology.edges_iter():
        if u in sources or v in sources:
            topology.edge[u][v]['type'] = 'external'
            fnss.set_delays_constant(topology, EXTERNAL_LINK_DELAY, 'ms', [(u, v)])
        else:
            topology.edge[u][v]['type'] = 'internal'
    cache_placement = uniform_cache_placement(topology, network_cache*n_contents, caches)
    for node, size in cache_placement.iteritems():
        fnss.add_stack(topology, node, 'cache', {'size': size})
    return topology


@register_topology_factory('GEANT')
def topology_geant(network_cache=0.05, n_contents=100000, seed=None):
    """
    Return a scenario based on GEANT topology
    
    Parameters
    ----------
    network_cache : float
        Size of network cache (sum of all caches) normalized by size of content
        population
    n_contents : int
        Size of content population
    seed : int, optional
        The seed used for random number generation
        
    Returns
    -------
    topology : fnss.Topology
        The topology object
    """
    # 240 nodes in the main component
    topology = fnss.parse_topology_zoo(path.join(TOPOLOGY_RESOURCES_DIR,
                                                 'Geant2012.graphml')
                                       ).to_undirected()
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
    content_placement = uniform_content_placement(topology, range(1, n_contents+1), sources, seed=seed)
    # add stacks to nodes
    for v in sources:
        fnss.add_stack(topology, v, 'source', {'contents': content_placement[v]})
    for v in receivers:
        fnss.add_stack(topology, v, 'receiver', {})
    for v in routers:
        fnss.add_stack(topology, v, 'router', {})
    # set weights and delays on all links
    fnss.set_weights_constant(topology, 1.0)
    fnss.set_delays_constant(topology, INTERNAL_LINK_DELAY, 'ms')
    # label links as internal or external
    for u, v in topology.edges_iter():
        if u in sources or v in sources:
            topology.edge[u][v]['type'] = 'external'
            # this prevents sources to be used to route traffic
            fnss.set_weights_constant(topology, 1000.0, [(u, v)])
            fnss.set_delays_constant(topology, EXTERNAL_LINK_DELAY, 'ms', [(u, v)])
        else:
            topology.edge[u][v]['type'] = 'internal'
    # place caches 
    cache_placement = uniform_cache_placement(topology, network_cache*n_contents, caches)
    for node, size in cache_placement.iteritems():
        fnss.add_stack(topology, node, 'cache', {'size': size})
    return topology


@register_topology_factory('TISCALI')
def topology_tiscali(network_cache=0.05, n_contents=100000, seed=None):
    """
    Return a scenario based on Tiscali topology, parsed from RocketFuel dataset
    
    Parameters
    ----------
    network_cache : float
        Size of network cache (sum of all caches) normalized by size of content
        population
    n_contents : int
        Size of content population
    seed : int, optional
        The seed used for random number generation
        
    Returns
    -------
    topology : fnss.Topology
        The topology object
    """
    # 240 nodes in the main component
    topology = fnss.parse_rocketfuel_isp_map(path.join(TOPOLOGY_RESOURCES_DIR,
                                                       '3257.r0.cch')
                                             ).to_undirected()
    topology = nx.connected_component_subgraphs(topology)[0]
    # degree of nodes
    deg = nx.degree(topology)
    # nodes with degree = 1
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
    fnss.set_delays_constant(topology, INTERNAL_LINK_DELAY, 'ms')
    # randomly allocate contents to sources
    content_placement = uniform_content_placement(topology, range(1, n_contents+1),
                                                  sources, seed=seed)
    for v in sources:
        fnss.add_stack(topology, v, 'source', {'contents': content_placement[v]})
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
            fnss.set_delays_constant(topology, EXTERNAL_LINK_DELAY, 'ms', [(u, v)])
        else:
            topology.edge[u][v]['type'] = 'internal'
            
    cache_placement = uniform_cache_placement(topology, network_cache*n_contents, caches)
    for node, size in cache_placement.iteritems():
        fnss.add_stack(topology, node, 'cache', {'size': size})
    return topology


@register_topology_factory('WIDE')
def topology_wide(network_cache=0.05, n_contents=100000, seed=None):
    """
    Return a scenario based on GARR topology
    
    Parameters
    ----------
    network_cache : float
        Size of network cache (sum of all caches) normalized by size of content
        population
    n_contents : int
        Size of content population
    seed : int, optional
        The seed used for random number generation
        
    Returns
    -------
    topology : fnss.Topology
        The topology object
    """
    topology = fnss.parse_topology_zoo(path.join(TOPOLOGY_RESOURCES_DIR, 'WideJpn.graphml')).to_undirected()
    # sources are nodes representing neighbouring AS's
    sources = [9, 8, 11, 13, 12, 15, 14, 17, 16, 19, 18]
    # receivers are internal nodes with degree = 1
    receivers = [27, 28, 3, 5, 4, 7]
    # caches are all remaining nodes --> 27 caches
    caches = [n for n in topology.nodes() if n not in receivers + sources]
    # set weights and delays on all links
    fnss.set_weights_constant(topology, 1.0)
    fnss.set_delays_constant(topology, INTERNAL_LINK_DELAY, 'ms')
    # randomly allocate contents to sources
    content_placement = uniform_content_placement(topology, range(1, n_contents+1),
                                                  sources, seed=seed)
    for v in sources:
        fnss.add_stack(topology, v, 'source', {'contents': content_placement[v]})
    for v in receivers:
        fnss.add_stack(topology, v, 'receiver', {})
    # label links as internal or external
    for u, v in topology.edges():
        if u in sources or v in sources:
            topology.edge[u][v]['type'] = 'external'
            # this prevents sources to be used to route traffic
            fnss.set_weights_constant(topology, 1000.0, [(u, v)])
            fnss.set_delays_constant(topology, EXTERNAL_LINK_DELAY, 'ms',[(u, v)])
        else:
            topology.edge[u][v]['type'] = 'internal'
    cache_placement = uniform_cache_placement(topology, network_cache*n_contents, caches)  
    for node, size in cache_placement.iteritems():
        fnss.add_stack(topology, node, 'cache', {'size': size})
    return topology


@register_topology_factory('GARR')
def topology_garr(network_cache=0.05, n_contents=100000, seed=None):
    """
    Return a scenario based on GARR topology
    
    Parameters
    ----------
    network_cache : float
        Size of network cache (sum of all caches) normalized by size of content
        population
    n_contents : int
        Size of content population
    seed : int, optional
        The seed used for random number generation
        
    Returns
    -------
    topology : fnss.Topology
        The topology object
    """
    topology = fnss.parse_topology_zoo(path.join(TOPOLOGY_RESOURCES_DIR, 'Garr201201.graphml')).to_undirected()
    # sources are nodes representing neighbouring AS's
    sources = [0, 2, 3, 5, 13, 16, 23, 24, 25, 27, 51, 52, 54]
    # receivers are internal nodes with degree = 1
    receivers = [1, 7, 8, 9, 11, 12, 19, 26, 28, 30, 32, 33, 41, 42, 43, 47, 48, 50, 53, 57, 60]
    # caches are all remaining nodes --> 27 caches
    caches = [n for n in topology.nodes() if n not in receivers + sources]
    # set weights and delays on all links
    fnss.set_weights_constant(topology, 1.0)
    fnss.set_delays_constant(topology, INTERNAL_LINK_DELAY, 'ms')

    # randomly allocate contents to sources
    content_placement = uniform_content_placement(topology, range(1, n_contents+1),
                                                  sources, seed=seed)
    for v in sources:
        fnss.add_stack(topology, v, 'source', {'contents': content_placement[v]})
    for v in receivers:
        fnss.add_stack(topology, v, 'receiver', {})
    
    # label links as internal or external
    for u, v in topology.edges():
        if u in sources or v in sources:
            topology.edge[u][v]['type'] = 'external'
            # this prevents sources to be used to route traffic
            fnss.set_weights_constant(topology, 1000.0, [(u, v)])
            fnss.set_delays_constant(topology, EXTERNAL_LINK_DELAY, 'ms',[(u, v)])
        else:
            topology.edge[u][v]['type'] = 'internal'
    cache_placement = uniform_cache_placement(topology, network_cache*n_contents, caches)  
    for node, size in cache_placement.iteritems():
        fnss.add_stack(topology, node, 'cache', {'size': size})
    return topology

