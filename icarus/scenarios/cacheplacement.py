"""Implements cache placement strategies
"""

import networkx as nx


__all__ = [
        'uniform_cache_placement',
          ]


def uniform_cache_placement(topology, cache_budget, cache_nodes, **kwargs):
    """Places cache budget uniformly across cache nodes.
    
    Parameters
    ----------
    topology : Topology
        The topology object
    cache_budget : int
        The cumulative cache budget
    cache_nodes : list
        List of nodes of the topology on which caches can be deployed
        
    Returns
    -------
    cache_placement : dict
        Dictionary mapping node to assigned cache space
    """
    cache_size = int(cache_budget//len(cache_nodes))
    return dict((v, cache_size) for v in cache_nodes)