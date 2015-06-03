"""Cache placement strategies

This module provides algorithms for performing cache placement, i.e. given
a cumulative cache size and a topology where each possible node candidate is
labelled, these functions deploy caching space to the nodes of the topology. 
"""
from __future__ import division
import networkx as nx

from icarus.util import iround
from icarus.registry import register_cache_placement

__all__ = [
        'uniform_cache_placement',
        'degree_centrality_cache_placement',
        'betweenness_centrality_cache_placement',
        'uniform_consolidated_cache_placement'
          ]


@register_cache_placement('UNIFORM')
def uniform_cache_placement(topology, cache_budget, **kwargs):
    """Places cache budget uniformly across cache nodes.
    
    Parameters
    ----------
    topology : Topology
        The topology object
    cache_budget : int
        The cumulative cache budget
    """
    icr_candidates = topology.graph['icr_candidates']
    cache_size = iround(cache_budget/len(icr_candidates))
    for v in icr_candidates:
        topology.node[v]['stack'][1]['cache_size'] = cache_size


@register_cache_placement('DEGREE')
def degree_centrality_cache_placement(topology, cache_budget, **kwargs):
    """Places cache budget proportionally to the degree of the node.
    
    Parameters
    ----------
    topology : Topology
        The topology object
    cache_budget : int
        The cumulative cache budget
    """
    deg = nx.degree(topology)
    total_deg = sum(deg.values())
    icr_candidates = topology.graph['icr_candidates']
    for v in icr_candidates:
        topology.node[v]['stack'][1]['cache_size'] = iround(cache_budget*deg[v]/total_deg)


@register_cache_placement('BETWEENNESS_CENTRALITY')
def betweenness_centrality_cache_placement(topology, cache_budget, **kwargs):
    """Places cache budget proportionally to the betweenness centrality of the
    node.
    
    Parameters
    ----------
    topology : Topology
        The topology object
    cache_budget : int
        The cumulative cache budget
    """
    betw = nx.betweenness_centrality(topology)
    total_betw = sum(betw.values())
    icr_candidates = topology.graph['icr_candidates']
    for v in icr_candidates:
        topology.node[v]['stack'][1]['cache_size'] = iround(cache_budget*betw[v]/total_betw)


@register_cache_placement('CONSOLIDATED')
def uniform_consolidated_cache_placement(topology, cache_budget, spread=0.5,
                                         metric_dict=None, target='top',
                                         **kwargs):
    """Consolidate caches in nodes with top centrality.
    
    Differently from other cache placement strategies that place cache space
    to all nodes but proportionally to their centrality, this strategy places
    caches of all the same size in a set of selected nodes.
    
    Parameters
    ----------
    topology : Topology
        The topology object
    cache_budget : int
        The cumulative cache budget
    spread : float [0, 1], optional
        The spread factor, The greater it is the more the cache budget is
        spread among nodes. If it is 1, all candidate nodes are assigned a
        cache, if it is 0, only the node with the highest/lowest centrality
        is assigned a cache
    metric_dict : dict, optional
        The centrality metric according to which nodes are selected. If not
        specified, betweenness centrality is selected.
    target : ("top" | "bottom"), optional
        The subsection of the ranked node on which to the deploy caches.
    """
    if spread < 0 or spread > 1:
        raise ValueError('spread factor must be between 0 and 1')
    if target not in ('top', 'bottom'):
        raise ValueError('target argument must be either "top" or "bottom"')
    if metric_dict is None and spread < 1:
        metric_dict = nx.betweenness_centrality(topology)
    
    icr_candidates = topology.graph['icr_candidates']
    if spread == 1:
        target_nodes = icr_candidates
    else:
        nodes = sorted(icr_candidates, key=lambda k: metric_dict[k])
        if target == 'top':
            nodes = list(reversed(nodes))
        # cutoff node must be at least one otherwise, if spread is too low, no
        # nodes would be selected
        cutoff = max(1, iround(spread*len(nodes)))
        target_nodes = nodes[:cutoff]
    cache_size = iround(cache_budget/len(target_nodes))
    if cache_size == 0:
        return
    for v in target_nodes:
        topology.node[v]['stack'][1]['cache_size'] = cache_size
