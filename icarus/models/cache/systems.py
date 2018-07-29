"""Simple networks of caches modeled as single caches."""
import random
import numpy as np

from icarus.util import inheritdoc
from icarus.tools import DiscreteDist
from icarus.registry import register_cache_policy, CACHE_POLICY

from .policies import Cache


__all__ = [
    'PathCache',
    'TreeCache',
    'ArrayCache',
    'ShardedCache',
           ]


@register_cache_policy('PATH')
class PathCache(object):
    """Path of caches

    This is not a single-node cache implementation but rather it implements
    a path of caching nodes in which requests are fed to the first node of the
    path and, in case of a miss, are propagated down to the remaining nodes
    of the path. A miss occurs if none of the nodes on the path has the
    requested content.
    """

    def __init__(self, caches, **kwargs):
        """Constructor

        Parameters
        ----------
        caches : array-like
            An array of caching nodes instances on the path
        """
        self._caches = caches
        self._len = len(caches)

    def __len__(self):
        return self._len

    @property
    def maxlen(self):
        return self._len

    def has(self, k):
        for c in self._caches:
            if c.has(k):
                return True
        else:
            return False

    def get(self, k):
        for i in range(self._len):
            if self._caches[i].get(k):
                break
        else:
            return False
        # Put contents on all caches traversed by the retrieved content
        for j in range(i):
            self._caches[j].put(k)
        return True

    def put(self, k):
        """Insert an item in the cache if not already inserted.

        If the element is already present in the cache, it will pushed to the
        top of the cache.

        Parameters
        ----------
        k : any hashable type
            The item to be inserted

        Returns
        -------
        evicted : any hashable type
            The evicted object or *None* if no contents were evicted.
        """
        for c in self._caches:
            c.put(k)

    def remove(self, k):
        raise NotImplementedError('This method is not implemented')

    def position(self, k):
        raise NotImplementedError('This method is not implemented')

    def dump(self, serialized=True):
        dump = [c.dump() for c in self._caches]
        return sum(dump, []) if serialized else dump

    def clear(self):
        for c in self._caches:
            c.clear()


@register_cache_policy('TREE')
class TreeCache(object):
    """Path of caches

    This is not a single-node cache implementation but rather it implements
    a tree of caching nodes in which requests are fed to a random leaf node
    and, in case of a miss, are propagated down to the remaining nodes
    of the path. A miss occurs if none of the nodes on the path has the
    requested content.

    Notes
    -----
    This cache can only be operated in a read-through manner and not in write
    through or read/write aside. In other words, before issuing a put, you
    must issue a get for the same item. The reason for this limitation is
    to ensure that matching get/put requests go through the same randomly
    selected node.
    """

    def __init__(self, leaf_caches, root_cache, **kwargs):
        """Constructor

        Parameters
        ----------
        caches : array-like
            An array of caching nodes instances on the path
        segments : int
            The number of segments
        """
        self._leaf_caches = leaf_caches
        self._root_cache = root_cache
        self._len = sum(len(c) for c in leaf_caches) + len(root_cache)
        self._n_leaves = len(leaf_caches)
        self._leaf = None

    def __len__(self):
        return self._len

    @property
    def maxlen(self):
        return self._len

    def has(self, k):
        raise NotImplementedError('This method is not implemented')

    def get(self, k):
        self._leaf = random.choice(self._leaf_caches)
        if self._leaf.get(k):
            return True
        else:
            if self._root_cache.get(k):
                self._leaf.put(k)
                return True
            else:
                return False

    def put(self, k):
        """Insert an item in the cache if not already inserted.

        If the element is already present in the cache, it will pushed to the
        top of the cache.

        Parameters
        ----------
        k : any hashable type
            The item to be inserted

        Returns
        -------
        evicted : any hashable type
            The evicted object or *None* if no contents were evicted.
        """
        if self._leaf is None:
            raise ValueError("You are trying to insert an item not requested before. "
                             "Tree cache can be used in read-through mode only")
        self._leaf.put(k)
        self._root_cache.put(k)

    def remove(self, k):
        raise NotImplementedError('This method is not implemented')

    def position(self, k):
        raise NotImplementedError('This method is not implemented')

    def dump(self, serialized=True):
        dump = [c.dump() for c in self._leaf_caches]
        dump.append(self._root_cache.dump())
        return sum(dump, []) if serialized else dump

    def clear(self):
        for c in self._caches:
            c.clear()


@register_cache_policy('ARRAY')
class ArrayCache(object):
    """Array of caches

    This is not a single-node cache implementation but rather it implements
    an array of caching nodes in which requests are fed to a random node of
    a set.

    Notes
    -----
    This cache can only be operated in a read-through manner and not in write
    through or read/write aside. In other words, before issuing a put, you
    must issue a get for the same item. The reason for this limitation is
    to ensure that matching get/put requests go through the same randomly
    selected node.
    """

    def __init__(self, caches, weights=None, **kwargs):
        """Constructor

        Parameters
        ----------
        caches : array-like
            An array of caching nodes instances on the array
        weights : array-like
            Random weights according to which a cache of the array should be
            selected to process a given request
        """
        self._caches = caches
        self._len = sum(len(c) for c in caches)
        self._n_caches = len(caches)
        self._selected_cache = None
        if weights is not None:
            if np.abs(np.sum(weights) - 1) > 0.0001:
                raise ValueError("weights must sum up to 1")
            if len(weights) != self._n_caches:
                raise ValueError("weights must have as many elements as nr of caches")
            randvar = DiscreteDist(weights)
            self.select_cache = lambda: self._caches[randvar.rv() - 1]
        else:
            self.select_cache = lambda: random.choice(self._caches)

    def __len__(self):
        return self._len

    @property
    def maxlen(self):
        return self._len

    def has(self, k):
        raise NotImplementedError('This method is not implemented')

    def get(self, k):
        self._selected_cache = self.select_cache()
        return self._selected_cache.get(k)

    def put(self, k):
        """Insert an item in the cache if not already inserted.

        If the element is already present in the cache, it will pushed to the
        top of the cache.

        Parameters
        ----------
        k : any hashable type
            The item to be inserted

        Returns
        -------
        evicted : any hashable type
            The evicted object or *None* if no contents were evicted.
        """
        if self._selected_cache is None:
            raise ValueError("You are trying to insert an item not requested before. "
                             "Array cache can be used in read-through mode only")
        self._selected_cache.put(k)

    def remove(self, k):
        raise NotImplementedError('This method is not implemented')

    def position(self, k):
        raise NotImplementedError('This method is not implemented')

    def dump(self, serialized=True):
        dump = [c.dump() for c in self._caches]
        return sum(dump, []) if serialized else dump

    def clear(self):
        for c in self._caches:
            c.clear()


@register_cache_policy('SHARD')
class ShardedCache(Cache):
    """Set of sharded caches.

    Set of caches coordinately storing items. When a request reaches the
    caches, the request is forwarded to the specific cache (shard) based on the
    outcome of a hash function. So, an item can be stored only by a single
    node of the system.
    """

    def __init__(self, maxlen, policy='LRU', nodes=4, f_map=None,
                 policy_attr={}, **kwargs):
        """Constructor

        Parameters
        ----------
        maxlen : int
            The maximum number of items the cache can store.
        policy : str, optional
            The eviction policy of each node (e.g., LRU, LFU, FIFO...).
            Default is LRU.
        nodes : int, optional
            The number of nodes, default is 4.
        f_map : callable, optional
            A callable governing the mapping between items and caching nodes.
            It receives as argument a value of an item :math:`k` and returns an
            integer between :math:`0` and :math:`nodes - 1` identifying the
            target node.
            If not specified, the mapping is done by computing the hash of the
            given item modulo the number of nodes.
        policy_attr : dict, optional
            A set of parameters for initializing the underlying caching policy.

        Notes
        -----
        The maxlen parameter refers to the cumulative size of the caches in the
        set. The size of each shard is derived dividing maxlen by the number
        of nodes.
        """
        maxlen = int(maxlen)
        if maxlen <= 0:
            raise ValueError('maxlen must be positive')
        if not isinstance(nodes, int) or nodes <= 0 or nodes > maxlen:
            raise ValueError('nodes must be an integer and 0 < nodes <= maxlen')
        # If maxlen is not a multiple of nodes, then some nodes have one slot
        # more than others
        self._node_maxlen = [maxlen // nodes for _ in range(nodes)]
        for i in range(maxlen % nodes):
            self._node_maxlen[i] += 1
        self._maxlen = maxlen
        self._node = [CACHE_POLICY[policy](self._node_maxlen[i], **policy_attr)
                      for i in range(nodes)]
        self.f_map = f_map if f_map is not None else lambda k: hash(k) % nodes

    @inheritdoc(Cache)
    def __len__(self):
        return sum(len(s) for s in self._node)

    @property
    def maxlen(self):
        return self._maxlen

    @inheritdoc(Cache)
    def has(self, k):
        return self._node[self.f_map(k)].has(k)

    @inheritdoc(Cache)
    def get(self, k):
        return self._node[self.f_map(k)].get(k)

    @inheritdoc(Cache)
    def put(self, k):
        return self._node[self.f_map(k)].put(k)

    @inheritdoc(Cache)
    def dump(self, serialized=True):
        dump = list(s.dump() for s in self._node)
        return sum(dump, []) if serialized else dump

    @inheritdoc(Cache)
    def remove(self, k):
        return self._node[self.f_map(k)].remove(k)

    @inheritdoc(Cache)
    def clear(self):
        for s in self._node:
            s.clear()
