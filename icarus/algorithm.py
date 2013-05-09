"""Algorithms for assigning contents to caches"""

def assign_caches(topology, cache_size, replicas, **kwargs):
    """
    Optimization algorithm that decides how to allocate intervals of hash
    space to various caches.
    
    It returns a dictionary of lists keyed by hash interval ID. Each list is
    the list of the caches that are authorized to store the content. A list is
    returned also in the case the number of replicas is 1.
    """
    cache_nodes = list(cache_size.keys())
    return dict([(i, cache_nodes[i]) for i in range(len(cache_size))])