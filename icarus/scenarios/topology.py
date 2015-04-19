"""This module contains functions for creating or importing topologies for the
experiments.
"""
from __future__ import division

from os import path

import networkx as nx
import fnss

from icarus.registry import register_topology_factory


__all__ = [
        'IcnTopology',
        'topology_binary_tree',
        'topology_path',
        'topology_geant',
        'topology_tiscali',
        'topology_wide',
        'topology_garr',
        'topology_generic_rocketfuel_latency'
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


class IcnTopology(fnss.Topology):
    
    def cache_nodes(self):
        return {v: self.node[v]['stack'][1]['cache_size']
                for v in self
                if 'stack' in self.node[v]
                and 'cache_size' in self.node[v]['stack'][1]
                }
        
    def sources(self):
        return [v for v in self
                if 'stack' in self.node[v]
                and self.node[v]['stack'][0] == 'source']
        
    def receivers(self):
        return [v for v in self
                if 'stack' in self.node[v]
                and self.node[v]['stack'][0] == 'receiver']

@register_topology_factory('BINARY_TREE')
def topology_binary_tree(**kwargs):
    """Returns a tree topology
    
    Parameters
    ----------
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
    routers = [v for v in topology.nodes_iter()
              if topology.node[v]['depth'] > 0
              and topology.node[v]['depth'] < h]
    topology.graph['icr_candidates'] = routers
    for v in sources:
        fnss.add_stack(topology, v, 'source')
    for v in receivers:
        fnss.add_stack(topology, v, 'receiver')
    for v in routers:
        fnss.add_stack(topology, v, 'router')
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
    return IcnTopology(topology)


@register_topology_factory('PATH')
def topology_path(n=3, **kwargs):
    """Return a scenario based on path topology
    
    Parameters
    ----------
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
    routers = range(1, n-1)
    sources = [n-1]
    topology.graph['icr_candidates'] = routers
    for v in sources:
        fnss.add_stack(topology, v, 'source')
    for v in receivers:
        fnss.add_stack(topology, v, 'receiver')
    for v in routers:
        fnss.add_stack(topology, v, 'router')
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
    return IcnTopology(topology)


@register_topology_factory('GEANT')
def topology_geant(**kwargs):
    """Return a scenario based on GEANT topology
    
    Parameters
    ----------
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
    topology = list(nx.connected_component_subgraphs(topology))[0]
    deg = nx.degree(topology)
    receivers = [v for v in topology.nodes() if deg[v] == 1] # 8 nodes
    icr_candidates = [v for v in topology.nodes() if deg[v] > 2] # 19 nodes
    # attach sources to topology
    source_attachments = [v for v in topology.nodes() if deg[v] == 2] # 13 nodes
    sources = []
    for v in source_attachments:
        u = v + 1000 # node ID of source
        topology.add_edge(v, u)
        sources.append(u)
    routers = [v for v in topology.nodes() if v not in sources + receivers]
    # add stacks to nodes
    topology.graph['icr_candidates'] = icr_candidates
    for v in sources:
        fnss.add_stack(topology, v, 'source')
    for v in receivers:
        fnss.add_stack(topology, v, 'receiver')
    for v in routers:
        fnss.add_stack(topology, v, 'router')
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
    return IcnTopology(topology)


@register_topology_factory('TISCALI')
def topology_tiscali(**kwargs):
    """Return a scenario based on Tiscali topology, parsed from RocketFuel dataset
    
    Parameters
    ----------
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
    topology = list(nx.connected_component_subgraphs(topology))[0]
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
    icr_candidates = [v for v in topology.nodes() if deg[v] >= 6] # 36 nodes
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
    routers = [v for v in topology.nodes() if v not in sources + receivers]

    # set weights and delays on all links
    fnss.set_weights_constant(topology, 1.0)
    fnss.set_delays_constant(topology, INTERNAL_LINK_DELAY, 'ms')
    
    # Deploy stacks
    topology.graph['icr_candidates'] = icr_candidates
    for v in sources:
        fnss.add_stack(topology, v, 'source')
    for v in receivers:
        fnss.add_stack(topology, v, 'receiver')
    for v in routers:
        fnss.add_stack(topology, v, 'router')

    # label links as internal or external
    for u, v in topology.edges():
        if u in sources or v in sources:
            topology.edge[u][v]['type'] = 'external'
            # this prevents sources to be used to route traffic
            fnss.set_weights_constant(topology, 1000.0, [(u, v)])
            fnss.set_delays_constant(topology, EXTERNAL_LINK_DELAY, 'ms', [(u, v)])
        else:
            topology.edge[u][v]['type'] = 'internal'
    return IcnTopology(topology)


@register_topology_factory('WIDE')
def topology_wide(**kwargs):
    """Return a scenario based on GARR topology
    
    Parameters
    ----------
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
    routers = [n for n in topology.nodes() if n not in receivers + sources]
    # All routers can be upgraded to ICN functionalitirs
    icr_candidates = routers
    # set weights and delays on all links
    fnss.set_weights_constant(topology, 1.0)
    fnss.set_delays_constant(topology, INTERNAL_LINK_DELAY, 'ms')
    # Deploy stacks
    topology.graph['icr_candidates'] = icr_candidates
    for v in sources:
        fnss.add_stack(topology, v, 'source')
    for v in receivers:
        fnss.add_stack(topology, v, 'receiver')
    for v in routers:
        fnss.add_stack(topology, v, 'router')
    # label links as internal or external
    for u, v in topology.edges():
        if u in sources or v in sources:
            topology.edge[u][v]['type'] = 'external'
            # this prevents sources to be used to route traffic
            fnss.set_weights_constant(topology, 1000.0, [(u, v)])
            fnss.set_delays_constant(topology, EXTERNAL_LINK_DELAY, 'ms',[(u, v)])
        else:
            topology.edge[u][v]['type'] = 'internal'
    return IcnTopology(topology)


@register_topology_factory('GARR')
def topology_garr(**kwargs):
    """Return a scenario based on GARR topology
    
    Parameters
    ----------
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
    routers = [n for n in topology.nodes() if n not in receivers + sources]
    icr_candidates = routers
    # set weights and delays on all links
    fnss.set_weights_constant(topology, 1.0)
    fnss.set_delays_constant(topology, INTERNAL_LINK_DELAY, 'ms')

    # Deploy stacks
    topology.graph['icr_candidates'] = icr_candidates
    for v in sources:
        fnss.add_stack(topology, v, 'source')
    for v in receivers:
        fnss.add_stack(topology, v, 'receiver')
    for v in routers:
        fnss.add_stack(topology, v, 'router')
    
    # label links as internal or external
    for u, v in topology.edges():
        if u in sources or v in sources:
            topology.edge[u][v]['type'] = 'external'
            # this prevents sources to be used to route traffic
            fnss.set_weights_constant(topology, 1000.0, [(u, v)])
            fnss.set_delays_constant(topology, EXTERNAL_LINK_DELAY, 'ms',[(u, v)])
        else:
            topology.edge[u][v]['type'] = 'internal'
    return IcnTopology(topology)



@register_topology_factory('GARR_2')
def topology_garr2(**kwargs):
    """Return a scenario based on GARR topology.
    
    Differently from plain GARR, this topology some receivers are appended to
    routers and only a subset of routers which are actually on the path of some
    traffic are selected to become ICN routers. These changes make this
    topology more realistic. 

    Parameters
    ----------
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
    # routers are all remaining nodes --> 27 caches
    routers = [n for n in topology.nodes_iter() if n not in receivers + sources]
    artificial_receivers = list(range(1000, 1000 + len(routers)))
    for i in range(len(routers)):
        topology.add_edge(routers[i], artificial_receivers[i])
    receivers += artificial_receivers
    # Caches to nodes with degree > 3 (after adding artificial receivers)
    degree = nx.degree(topology)
    icr_candidates = [n for n in topology.nodes_iter() if degree[n] > 3.5]
    # set weights and delays on all links
    fnss.set_weights_constant(topology, 1.0)
    fnss.set_delays_constant(topology, INTERNAL_LINK_DELAY, 'ms')
    
    # Deploy stacks
    topology.graph['icr_candidates'] = icr_candidates
    for v in sources:
        fnss.add_stack(topology, v, 'source')
    for v in receivers:
        fnss.add_stack(topology, v, 'receiver')
    for v in routers:
        fnss.add_stack(topology, v, 'router')
    # label links as internal or external
    for u, v in topology.edges():
        if u in sources or v in sources:
            topology.edge[u][v]['type'] = 'external'
            # this prevents sources to be used to route traffic
            fnss.set_weights_constant(topology, 1000.0, [(u, v)])
            fnss.set_delays_constant(topology, EXTERNAL_LINK_DELAY, 'ms',[(u, v)])
        else:
            topology.edge[u][v]['type'] = 'internal'
    return IcnTopology(topology)


@register_topology_factory('GEANT_2')
def topology_geant2(**kwargs):
    """Return a scenario based on GEANT topology.
    
    Differently from plain GEANT, this topology some receivers are appended to
    routers and only a subset of routers which are actually on the path of some
    traffic are selected to become ICN routers. These changes make this
    topology more realistic.
     
    Parameters
    ----------
    seed : int, optional
        The seed used for random number generation
        
    Returns
    -------
    topology : fnss.Topology
        The topology object
    """
    # 53 nodes
    topology = fnss.parse_topology_zoo(path.join(TOPOLOGY_RESOURCES_DIR,
                                                 'Geant2012.graphml')
                                       ).to_undirected()
    topology = list(nx.connected_component_subgraphs(topology))[0]
    deg = nx.degree(topology)
    receivers = [v for v in topology.nodes() if deg[v] == 1] # 8 nodes
    # attach sources to topology
    source_attachments = [v for v in topology.nodes() if deg[v] == 2] # 13 nodes
    sources = []
    for v in source_attachments:
        u = v + 1000 # node ID of source
        topology.add_edge(v, u)
        sources.append(u)
    routers = [v for v in topology.nodes() if v not in sources + receivers]
    # Put caches in nodes with top betweenness centralities
    betw = nx.betweenness_centrality(topology)
    routers = sorted(routers, key=lambda k: betw[k])
    # Select as ICR candidates the top 50% routers for betweenness centrality
    icr_candidates = routers[len(routers)//2:] 
    # add stacks to nodes
    topology.graph['icr_candidates'] = icr_candidates
    for v in sources:
        fnss.add_stack(topology, v, 'source')
    for v in receivers:
        fnss.add_stack(topology, v, 'receiver')
    for v in routers:
        fnss.add_stack(topology, v, 'router')
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
    return IcnTopology(topology)

@register_topology_factory('TISCALI_2')
def topology_tiscali2(**kwargs):
    """Return a scenario based on Tiscali topology, parsed from RocketFuel dataset

    Differently from plain Tiscali, this topology some receivers are appended to
    routers and only a subset of routers which are actually on the path of some
    traffic are selected to become ICN routers. These changes make this
    topology more realistic. 

    Parameters
    ----------
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
    topology = list(nx.connected_component_subgraphs(topology))[0]
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
    icr_candidates = [v for v in topology.nodes() if deg[v] >= 6] # 36 nodes
    # Add remove caches to adapt betweenness centrality of caches
    for i in [181, 208, 211, 220, 222, 250, 257]:
        icr_candidates.remove(i)
    icr_candidates.extend([232, 303, 326, 363, 378])
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
    routers = [v for v in topology.nodes() if v not in sources + receivers]

    # set weights and delays on all links
    fnss.set_weights_constant(topology, 1.0)
    fnss.set_delays_constant(topology, INTERNAL_LINK_DELAY, 'ms')
    
    # deploy stacks
    topology.graph['icr_candidates'] = icr_candidates
    for v in sources:
        fnss.add_stack(topology, v, 'source')
    for v in receivers:
        fnss.add_stack(topology, v, 'receiver')
    for v in routers:
        fnss.add_stack(topology, v, 'router')

    # label links as internal or external
    for u, v in topology.edges():
        if u in sources or v in sources:
            topology.edge[u][v]['type'] = 'external'
            # this prevents sources to be used to route traffic
            fnss.set_weights_constant(topology, 1000.0, [(u, v)])
            fnss.set_delays_constant(topology, EXTERNAL_LINK_DELAY, 'ms', [(u, v)])
        else:
            topology.edge[u][v]['type'] = 'internal'
    return IcnTopology(topology)


@register_topology_factory('ROCKET_FUEL')
def topology_generic_rocketfuel_latency(asn, source_ratio, ext_delay, **kwargs):
    """Parse a generic RocketFuel topology with annotated latencies
    
    To each node of the parsed topology it is attached an artificial receiver
    node. To the routers with highest degree it is also attached a source node. 
    
    Parameters
    ----------
    asn : int
        AS number
    source_ratio : float
        Ratio between number of source nodes (artificially attached) and routers
    ext_delay : float
        Delay on external nodes
    """
    if source_ratio < 0 or source_ratio > 1:
        raise ValueError('source_ratio must be comprised between 0 and 1')
    f_topo = path.join(TOPOLOGY_RESOURCES_DIR, 'rocketfuel-latency', str(asn), 'latencies.intra')
    topology = fnss.parse_rocketfuel_isp_latency(f_topo).to_undirected()
    topology = list(nx.connected_component_subgraphs(topology))[0]
    # Note: I don't need to filter out nodes with degree 1 cause they all have
    # a greater degree value but we compute degree to decide where to attach sources
    routers = topology.nodes()
    deg = nx.degree(topology)
    routers = sorted(routers, key=lambda k: deg[k], reverse=True)
    # Source attachment
    n_sources = int(source_ratio*len(routers))
    sources = ['src_%d' % i for i in range(n_sources)]
    for i in range(len(sources)):
        topology.add_edge(sources[i], routers[i], delay=ext_delay)
    
    # attach artificial receiver nodes to ICR candidates
    receivers = ['rec_%d' % i for i in range(len(routers))]
    for i in range(len(routers)):
        topology.add_edge(receivers[i], routers[i], delay=0)
    # Set weights to latency values
    for u, v in topology.edges_iter():
        topology.edge[u][v]['weight'] = topology.edge[u][v]['delay']
    # Deploy stacks on nodes
    topology.graph['icr_candidates'] = routers
    for v in sources:
        fnss.add_stack(topology, v, 'source')
    for v in receivers:
        fnss.add_stack(topology, v, 'receiver')
    for v in routers:
        fnss.add_stack(topology, v, 'router')
    return topology
    
