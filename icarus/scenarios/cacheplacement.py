"""Cache placement strategies

This module provides algorithms for performing cache placement, i.e., given
a cumulative cache size and a topology where each possible node candidate is
labelled, these functions deploy caching space to the nodes of the topology.
"""
from __future__ import division
import random
import networkx as nx

from icarus.util import iround
from icarus.registry import register_cache_placement
from icarus.scenarios.algorithms import compute_clusters, compute_p_median, deploy_clusters

__all__ = [
    'uniform_cache_placement',
    'degree_centrality_cache_placement',
    'betweenness_centrality_cache_placement',
    'uniform_consolidated_cache_placement',
    'random_cache_placement',
    'optimal_median_cache_placement',
    'optimal_hashrouting_cache_placement',
    'clustered_hashrouting_cache_placement',
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
    cache_size = iround(cache_budget / len(icr_candidates))
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
    deg = dict(nx.degree(topology))
    icr_candidates = set(topology.graph['icr_candidates'])
    total_deg = sum(v for k, v in deg.items() if k in icr_candidates)
    for v in icr_candidates:
        topology.node[v]['stack'][1]['cache_size'] = iround(cache_budget * deg[v] / total_deg)


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
    betw = dict(nx.betweenness_centrality(topology))
    icr_candidates = set(topology.graph['icr_candidates'])
    total_betw = sum(v for k, v in betw.items() if k in icr_candidates)
    for v in icr_candidates:
        topology.node[v]['stack'][1]['cache_size'] = iround(cache_budget * betw[v] / total_betw)


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
        cutoff = max(1, iround(spread * len(nodes)))
        target_nodes = nodes[:cutoff]
    cache_size = iround(cache_budget / len(target_nodes))
    if cache_size == 0:
        return
    for v in target_nodes:
        topology.node[v]['stack'][1]['cache_size'] = cache_size


@register_cache_placement('RANDOM')
def random_cache_placement(topology, cache_budget, n_cache_nodes,
                           seed=None, **kwargs):
    """Deploy caching nodes randomly

    Parameters
    ----------
    topology : Topology
        The topology object
    cache_budget : int
        The cumulative cache budget
    n_nodes : int
        The number of caching nodes to deploy
    """
    n_cache_nodes = int(n_cache_nodes)
    icr_candidates = topology.graph['icr_candidates']
    if len(icr_candidates) < n_cache_nodes:
        raise ValueError("The number of ICR candidates is lower than the target number of caches")
    elif len(icr_candidates) == n_cache_nodes:
        caches = icr_candidates
    else:
        random.seed(seed)
        caches = random.sample(icr_candidates, n_cache_nodes)
    cache_size = iround(cache_budget / n_cache_nodes)
    if cache_size == 0:
        return
    for v in caches:
        topology.node[v]['stack'][1]['cache_size'] = cache_size


@register_cache_placement('OPTIMAL_MEDIAN')
def optimal_median_cache_placement(topology, cache_budget, n_cache_nodes,
                                   hit_ratio, weight='delay', **kwargs):
    """Deploy caching nodes in locations that minimize overall latency assuming
    a partitioned strategy (a la Google Global Cache). According to this, in
    the network, a set of caching nodes are deployed and each receiver is
    mapped to one and only one caching node. Requests from this receiver are
    always sent to the designated caching node. In case of cache miss requests
    are forwarded to the original source.

    This placement problem can be mapped to the p-median location-allocation
    problem. This function solves this problem using the vertex substitution
    heuristic, which practically works like the k-medoid PAM algorithms, which
    is also similar to the k-means clustering algorithm. The result is not
    guaranteed to be globally optimal, only locally optimal.

    Notes
    -----
    This placement assumes that all receivers have degree = 1 and are connected
    to an ICR candidate nodes. Also, it assumes that contents are uniformly
    assigned to sources.

    Parameters
    ----------
    topology : Topology
        The topology object
    cache_budget : int
        The cumulative cache budget
    n_nodes : int
        The number of caching nodes to deploy
    hit_ratio : float
        The expected cache hit ratio of a single cache
    weight : str
        The weight attribute
    """
    n_cache_nodes = int(n_cache_nodes)
    icr_candidates = topology.graph['icr_candidates']
    if len(icr_candidates) < n_cache_nodes:
        raise ValueError("The number of ICR candidates (%d) is lower than "
                         "the target number of caches (%d)"
                         % (len(icr_candidates), n_cache_nodes))
    elif len(icr_candidates) == n_cache_nodes:
        caches = list(icr_candidates)
        cache_assignment = {v: list(topology.adj[v].keys())[0]
                            for v in topology.receivers()}
    else:
        # Need to optimally allocate caching nodes
        distances = dict(nx.all_pairs_dijkstra_path_length(topology, weight=weight))
        sources = topology.sources()
        d = {u: {} for u in icr_candidates}
        for u in icr_candidates:
            source_dist = sum(distances[u][source] for source in sources) / len(sources)
            for v in icr_candidates:
                if v in d[u]:
                    d[v][u] = d[u][v]
                else:
                    d[v][u] = distances[v][u] + (hit_ratio * source_dist)
        allocation, caches, _ = compute_p_median(distances, n_cache_nodes)
        cache_assignment = {v: allocation[list(topology.adj[v].keys())[0]]
                            for v in topology.receivers()}

    cache_size = iround(cache_budget / n_cache_nodes)
    if cache_size == 0:
        raise ValueError("Cache budget is %d but it's too small to deploy it on %d nodes. "
                         "Each node will have a zero-sized cache. "
                         "Set a larger cache budget and try again"
                         % (cache_budget, n_cache_nodes))
    for v in caches:
        topology.node[v]['stack'][1]['cache_size'] = cache_size
    topology.graph['cache_assignment'] = cache_assignment


@register_cache_placement('OPTIMAL_HASHROUTING')
def optimal_hashrouting_cache_placement(topology, cache_budget, n_cache_nodes,
                                        hit_ratio, weight='delay', **kwargs):
    """Deploy caching nodes for hashrouting in optimized location

    Parameters
    ----------
    topology : Topology
        The topology object
    cache_budget : int
        The cumulative cache budget
    n_nodes : int
        The number of caching nodes to deploy
    hit_ratio : float
        The expected global cache hit ratio
    weight : str, optional
        The weight attribute. Default is 'delay'

    References
    ----------
    .. [1] L. Saino, I. Psaras and G. Pavlou, Framework and Algorithms for
           Operator-managed Content Caching, in IEEE Transactions on
           Network and Service Management (TNSM), Volume 17, Issue 1, March 2020
           https://doi.org/10.1109/TNSM.2019.2956525
    .. [2] L. Saino, On the Design of Efficient Caching Systems, Ph.D. thesis
           University College London, Dec. 2015. Available:
           http://discovery.ucl.ac.uk/1473436/
    """
    n_cache_nodes = int(n_cache_nodes)
    icr_candidates = topology.graph['icr_candidates']
    if len(icr_candidates) < n_cache_nodes:
        raise ValueError("The number of ICR candidates (%d) is lower than "
                         "the target number of caches (%d)"
                         % (len(icr_candidates), n_cache_nodes))
    elif len(icr_candidates) == n_cache_nodes:
        caches = list(icr_candidates)
    else:
        # Need to optimally allocate caching nodes
        distances = dict(nx.all_pairs_dijkstra_path_length(topology, weight=weight))
        d = {}
        for v in icr_candidates:
            d[v] = 0
            for r in topology.receivers():
                d[v] += distances[r][v]
            for s in topology.sources():
                d[v] += distances[v][s] * hit_ratio

        # Sort caches in increasing order of distances and assign cache sizes
        caches = sorted(icr_candidates, key=lambda k: d[k])
    cache_size = iround(cache_budget / n_cache_nodes)
    if cache_size == 0:
        raise ValueError("Cache budget is %d but it's too small to deploy it on %d nodes. "
                         "Each node will have a zero-sized cache. "
                         "Set a larger cache budget and try again"
                         % (cache_budget, n_cache_nodes))
    for v in caches[:n_cache_nodes]:
        topology.node[v]['stack'][1]['cache_size'] = cache_size


@register_cache_placement('CLUSTERED_HASHROUTING')
def clustered_hashrouting_cache_placement(topology, cache_budget, n_clusters,
                            policy, distance='delay', **kwargs):
    """Deploy caching nodes for hashrouting in with clusters

    Parameters
    ----------
    topology : Topology
        The topology object
    cache_budget : int
        The cumulative cache budget
    n_clusters : int
        The number of clusters
    policy : str (node_const | cluster_const)
        The expected global cache hit ratio
    distance : str
        The attribute used to quantify distance between pairs of nodes.
        Default is 'delay'

    References
    ----------
    .. [1] L. Saino, I. Psaras and G. Pavlou, Framework and Algorithms for
           Operator-managed Content Caching, in IEEE Transactions on
           Network and Service Management (TNSM), Volume 17, Issue 1, March 2020
           https://doi.org/10.1109/TNSM.2019.2956525
    .. [2] L. Saino, On the Design of Efficient Caching Systems, Ph.D. thesis
           University College London, Dec. 2015. Available:
           http://discovery.ucl.ac.uk/1473436/
    """
    icr_candidates = topology.graph['icr_candidates']
    if n_clusters <= 0 or n_clusters > len(icr_candidates):
        raise ValueError("The number of cluster must be positive and <= the "
                         "number of ICR candidate nodes")
    elif n_clusters == 1:
        clusters = [set(icr_candidates)]
    elif n_clusters == len(icr_candidates):
        clusters = [set([v]) for v in icr_candidates]
    else:
        clusters = compute_clusters(topology, n_clusters, distance=distance,
                                    nbunch=icr_candidates, n_iter=100)
    deploy_clusters(topology, clusters, assign_src_rcv=True)
    if policy == 'node_const':
        # Each node is assigned the same amount of caching space
        cache_size = iround(cache_budget / len(icr_candidates))
        if cache_size == 0:
            return
        for v in icr_candidates:
            topology.node[v]['stack'][1]['cache_size'] = cache_size
    elif policy == 'cluster_const':
        cluster_cache_size = iround(cache_budget / n_clusters)
        for cluster in topology.graph['clusters']:
            cache_size = iround(cluster_cache_size / len(cluster))
            for v in cluster:
                if v not in icr_candidates:
                    continue
                topology.node[v]['stack'][1]['cache_size'] = cache_size
    else:
        raise ValueError('clustering policy %s not supported' % policy)
