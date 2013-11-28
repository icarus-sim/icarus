"""Content placement strategies.

This module contains function to decide the allocation of content objects to
source nodes.
"""
import random
import collections

from fnss.util import random_from_pdf


__all__ = ['uniform_content_placement', 'weighted_content_placement']


def uniform_content_placement(topology, contents, source_nodes, seed=None):
    """Places content objects to source nodes randomly following a uniform
    distribution.
    
    Parameters
    ----------
    topology : Topology
        The topology object
   contents : list
        List of content objects
    source_nodes : list
        List of nodes of the topology which are content sources
        
    Returns
    -------
    cache_placement : dict
        Dictionary mapping content objects to source nodes
    
    Notes
    -----
    A deterministic placement of objects (e.g., for reproducing results) can be
    achieved by using a fix seed value
    """
    random.seed(seed)
    content_placement = collections.defaultdict(list)
    for c in contents:
        content_placement[random.choice(source_nodes)].append(c)
    return content_placement
    
def weighted_content_placement(topology, contents, source_weights, seed=None):
    """Places content objects to source nodes randomly according to the weight
    of the source node.
    
    Parameters
    ----------
    topology : Topology
        The topology object
   contents : list
        List of content objects
    source_weights : dict
        Dict mapping nodes nodes of the topology which are content sources and
        the weight according to which content placement decision is made.
        
    Returns
    -------
    cache_placement : dict
        Dictionary mapping content objects to source nodes

    
    Notes
    -----
    A deterministic placement of objects (e.g., for reproducing results) can be
    achieved by using a fix seed value
    """
    random.seed(seed)
    norm_factor = float(sum(source_weights.values()))
    source_pdf = dict((k, v/norm_factor) for k, v in source_weights.iteritems())
    content_placement = collections.defaultdict(list)
    for c in contents:
        content_placement[random_from_pdf(source_pdf)].append(c)
    return content_placement
    