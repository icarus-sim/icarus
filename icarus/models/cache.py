"""Cache replacement policies implementations

This module contains the implementations of all the cache replacement policies
provided by Icarus.
"""
from collections import deque
import random
import abc

import numpy as np

from icarus.util import inheritdoc
from icarus.registry import register_cache_policy


__all__ = [
        'Node',
        'Cache',
        'NullCache',
        'LruCache',
        'LfuCache',
        'FifoCache',
        'RandCache',
        'set_rand_insert'
           ]


class Node(object):
    """Node of a linked list
    
    This class is used for implementing cache eviction policies relying on
    doubly-linked lists for their implementation.
    
    This class is used for example by the LRU replacement policy.
    """
    __metaclass__ = abc.ABCMeta
    
    def __init__(self, down, val):
        """
        Constructor
        
        Parameters
        ----------
        down : Node
            Pointer to the.downious node of the list
        val : any hashable type
            Object stored by this node
        """
        self.down = down        # Pointer to node down the chain
        self.val = val          # Object stored by this node
        self.up = None          # Pointer to node up the chain
        self.hits = 0           # Number of hits of this object
        self.time = 0           # Time this object was created


class Cache(object):
    """Base implementation of a cache object"""
    
    @abc.abstractmethod
    def __init__(self, maxlen):
        """Constructor
        
        Parameters
        ----------
        maxlen : int
            The maximum number of items the cache can store
        """
        raise NotImplementedError('This method is not implemented')
    
    @abc.abstractmethod
    def __len__(self):
        """Return the number of items currently stored in the cache
        
        Returns
        -------
        len : int
            The number of items currently in the cache
        """
        raise NotImplementedError('This method is not implemented')
    
    @property
    @abc.abstractmethod
    def maxlen(self):
        """Return the maximum number of items the cache can store
        
        Return
        ------
        maxlen : int
            The maximum number of items the cache can store 
        """
        raise NotImplementedError('This method is not implemented')

    @abc.abstractmethod
    def dump(self):
        """Return a dump of all the elements currently in the cache possibly
        sorted according to the eviction policy.
        
        Return
        ------
        cache_dump : list
            The list of all items currently stored in the cache
        """
        raise NotImplementedError('This method is not implemented')

    @abc.abstractmethod
    def has(self, k):
        """Check if an item is in the cache without changing the internal
        state of the caching object.
        
        Parameters
        ----------
        k : any hashable type
            The item looked up in the cache

        Returns
        -------
        v : bool
            Boolean value being *True* if the requested item is in the cache
            or *False* otherwise
        """
        raise NotImplementedError('This method is not implemented')    

    @abc.abstractmethod
    def get(self, k):
        """Retrieves an item from the cache. Differently from *has(k)*,
        calling this method may change the internal state of the caching
        object depending on the specific cache implementation.
        
        Parameters
        ----------
        k : any hashable type
            The item looked up in the cache

        Returns
        -------
        v : bool
            Boolean value being *True* if the requested item is in the cache
            or *False* otherwise
        """
        raise NotImplementedError('This method is not implemented') 

    @abc.abstractmethod
    def put(self, k):
        """Insert an item in the cache if not already inserted.
        
        If the element is already present in the cache, it will not be inserted
        again but the internal state of the cache object may change.
        
        Parameters
        ----------
        k : any hashable type
            The item to be inserted
            
        Returns
        -------
        evicted : any hashable type
            The evicted object or *None* if no contents were evicted.
        """
        raise NotImplementedError('This method is not implemented')
    
    @abc.abstractmethod
    def clear(self):
        """Empty the cache
        """
        raise NotImplementedError('This method is not implemented')



@register_cache_policy('NULL')
class NullCache(Cache):
    """Implementation of a null cache.
    
    This is a dummy cache which never stores anything. It is functionally
    identical to a cache with max size equal to 0.
    """
     
    def __init__(self, maxlen=0):
        """
        Constructor
        
        Parameters
        ----------
        maxlen : int, optional
            The max length of the cache. This parameters is always ignored
        """
        pass

    def __len__(self):
        """Return the number of items currently stored in the cache.
        
        Since this is a dummy cache implementation, it is always empty
        
        Returns
        -------
        len : int
            The number of items currently in the cache. It is always 0.
        """
        return 0
    
    @property
    def maxlen(self):
        """Return the maximum number of items the cache can store.
        
        Since this is a dummy cache implementation, this value is 0.
        
        Return
        ------
        maxlen : int
            The maximum number of items the cache can store. It is always 0
        """
        return 0
    
    def dump(self):
        """Return a list of all the elements currently in the cache.
        
        In this case it is always an empty list.
        
        Return
        ------
        cache_dump : list
            An empty list.
        """
        return []

    def has(self, k):
        """Check if an item is in the cache without changing the internal
        state of the caching object.
        
        Parameters
        ----------
        k : any hashable type
            The item looked up in the cache

        Returns
        -------
        v : bool
            Boolean value being *True* if the requested item is in the cache
            or *False* otherwise. It alwasy returns *False*
        """
        return False

    def get(self, k):
        """Retrieves an item from the cache.
        
        Parameters
        ----------
        k : any hashable type
            The item looked up in the cache

        Returns
        -------
        v : bool
            Boolean value being *True* if the requested item is in the cache
            or *False* otherwise. It always returns False
        """
        return False

    def put(self, k):
        """Insert an item in the cache if not already inserted.
        
        Parameters
        ----------
        k : any hashable type
            The item to be inserted
            
        Returns
        -------
        evicted : any hashable type
            The evicted object or *None* if no contents were evicted.
        """
        return None

    @inheritdoc(Cache)
    def clear(self):
        pass


@register_cache_policy('LRU')
class LruCache(Cache):
    """Least Recently Used (LRU) cache eviction policy.
    
    According to this policy, When a new item needs to inserted into the cache,
    it evicts the least recently requested one.
    This eviction policy is efficient for line speed operations because both
    search and replacement tasks can be performed in constant time (*O(1)*).
    
    This policy has been shown to perform well in the presence of temporal
    locality in the request pattern. However, its performance drops under the
    Independent Reference Model (IRM) assumption (i.e. the probability that an
    item is requested is not dependent on previous requests).
    """
        
    @inheritdoc(Cache)
    def __init__(self, maxlen):
        self._cache = {}
        self.bottom = None
        self.top = None
        self._maxlen = int(maxlen)
        if self._maxlen <= 0:
            raise ValueError('maxlen must be positive')

    @inheritdoc(Cache)
    def __len__(self):
        return len(self._cache)
    
    @property
    @inheritdoc(Cache)
    def maxlen(self):
        return self._maxlen
    
    @inheritdoc(Cache)
    def dump(self):
        d = deque()
        cur = self.top
        while cur:
            d.append(cur.val)
            cur = cur.down
        return list(d)

    def position(self, k):
        """Return the current position of an item in the cache. Position *0*
        refers to the head of cache (i.e. most recently used item), while
        position *maxlen - 1* refers to the tail of the cache (i.e. the least
        recently used item).
        
        This method does not change the internal state of the cache.
        
        Parameters
        ----------
        k : any hashable type
            The item looked up in the cache
            
        Returns
        -------
        position : int
            The current position of the item in the cache
        """
        if not k in self._cache:
            raise ValueError('The item %s is not in the cache' % str(k))
        index = 0
        cur = self.top
        while cur:
            if cur.val == k:
                return index
            cur = cur.down
            index += 1

    @inheritdoc(Cache)
    def has(self, k):
        return k in self._cache
            
    @inheritdoc(Cache)
    def get(self, k):
        # search content over the list
        # if it has it push on top, otherwise return false
        if not self.has(k):
            return False
        node = self._cache[k]
        if not node.up:
            return True # Content is already on top
        if node.down:
            node.down.up = node.up
        else:
            self.bottom = node.up # The.bottom node (bottom) now points to the 2nd node
        node.up.down = node.down
        del self._cache[k]
        obj = Node(self.top, k)
        if self.bottom is None:
            self.bottom = obj
        if self.top:
            self.top.up = obj
        self.top = obj
        self._cache[k] = obj
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
        # if content in cache, push it on top
        if self.get(k):
            return None
        # if content not in cache append it on top
        obj = Node(self.top, k)
        if self.bottom is None:
            self.bottom = obj
        if self.top:
            self.top.up = obj
        self.top = obj
        self._cache[k] = obj
        # If I reach cache size limit, evict a content
        if len(self._cache) <= self.maxlen:
            return None    
        if self.bottom == self.top:
            self.bottom = None
            self.top = None
            return None
        a = self.bottom
        evicted = a.val
        a.up.down = None
        self.bottom = a.up
        a.up = None
        del self._cache[evicted]
        del a
        return evicted

    @inheritdoc(Cache)
    def clear(self):
        self._cache.clear()
        self.bottom = None
        self.top = None


            

@register_cache_policy('LFU')
class LfuCache(Cache):
    """Least Frequently Used (LFU) cache implementation
    
    The LFU replacement policy keeps a counter associated each item. Such
    counters are increased when the associated item is requested. Upon
    insertion of a new item, the cache evicts the one which was requested the
    least times in the past, i.e. the one whose associated value has the
    smallest value.
    
    In contrast to LRU, LFU has been shown to perform optimally under IRM
    demands. However, its implementation is computationally expensive since it
    cannot be implemented in such a way that both search and replacement tasks
    can be executed in constant time. This makes it particularly unfit for
    large caches and line speed operations.
    """
    
    @inheritdoc(Cache)
    def __init__(self, maxlen):
        self._cache = {}
        self.t = 0
        self._maxlen = int(maxlen)
        if self._maxlen <= 0:
            raise ValueError('maxlen must be positive')

    @inheritdoc(Cache)
    def __len__(self):
        return len(self._cache)
    
    @property
    @inheritdoc(Cache)
    def maxlen(self):
        return self._maxlen
    
    @inheritdoc(Cache)
    def dump(self):
        return sorted(self._cache, key=lambda x: self._cache[x], reverse=True) 

    @inheritdoc(Cache)
    def has(self, k):
        return k in self._cache

    @inheritdoc(Cache)
    def get(self, k):
        if self.has(k):
            freq, t = self._cache[k]
            self._cache[k] = freq+1, t 
            return True
        else:
            return False

    @inheritdoc(Cache)
    def put(self, k):
        if not self.has(k):
            self.t += 1
            self._cache[k] = (1, self.t)
            if len(self._cache) > self._maxlen:
                evicted = min(self._cache, key=lambda x: self._cache[x])
                del self._cache[evicted]
                return evicted
        return None
        
    @inheritdoc(Cache)
    def clear(self):
        self._cache.clear()



@register_cache_policy('FIFO')
class FifoCache(Cache):
    """First In First Out (FIFO) cache implementation.
    
    According to the FIFO policy, when a new item is inserted, the evicted item
    is the first one inserted in the cache. The behavior of this policy differs
    from LRU only when an item already present in the cache is requested.
    In fact, while in LRU this item would be pushed to the top of the cache, in
    FIFO no movement is performed. The FIFO policy has a slightly simpler
    implementation in comparison to the LRU policy but yields worse performance.
    """
    
    @inheritdoc(Cache)
    def __init__(self, maxlen):
        self._cache = set()
        self._maxlen = int(maxlen)
        self.d = deque()
        if self._maxlen <= 0:
            raise ValueError('maxlen must be positive')
    
    @inheritdoc(Cache)
    def __len__(self):
        return len(self._cache)

    @property
    @inheritdoc(Cache)
    def maxlen(self):
        return self._maxlen
    
    @inheritdoc(Cache)
    def dump(self):
        return list(self.d)

    @inheritdoc(Cache)
    def has(self, k):
        return k in self._cache

    def position(self, k):
        """Return the current position of an item in the cache. Position *0*
        refers to the head of cache (i.e. most recently inserted item), while
        position *maxlen - 1* refers to the tail of the cache (i.e. the least
        recently inserted item).
        
        This method does not change the internal state of the cache.
        
        Parameters
        ----------
        k : any hashable type
            The item looked up in the cache
            
        Returns
        -------
        position : int
            The current position of the item in the cache
        """
        i = 0
        for c in self.d:
            if c == k:
                return i
            i += 1
        raise ValueError('The item %s is not in the cache' % str(k))
                 
    @inheritdoc(Cache)
    def get(self, k):
        return self.has(k)
             
    @inheritdoc(Cache)
    def put(self, k):
        evicted = None
        if not self.has(k):
            self._cache.add(k)
            self.d.appendleft(k)
        if len(self._cache) > self.maxlen:
            evicted = self.d.pop()
            self._cache.remove(evicted)
        return evicted
    
    @inheritdoc(Cache)
    def clear(self):
        self._cache.clear()
        self.d.clear()


@register_cache_policy('RAND')
class RandCache(Cache):
    """Random eviction cache implementation.
    
    This class implements a cache whereby the item to evict in case of a full
    cache is randomly selected. It generally yields poor performance in terms
    of cache hits but is sometimes used as baseline and for this reason it has
    been implemented here.
    """
    
    @inheritdoc(Cache)
    def __init__(self, maxlen):
        self._cache = set()
        self.a = np.empty(maxlen, dtype=object)
        self._maxlen = int(maxlen)
        if self._maxlen <= 0:
            raise ValueError('maxlen must be positive')

    @inheritdoc(Cache)
    def __len__(self):
        return len(self._cache)

    @property
    def maxlen(self):
        return self._maxlen

    @inheritdoc(Cache)
    def dump(self):
        return list(self._cache) 

    @inheritdoc(Cache)
    def has(self, k):
        return k in self._cache

    @inheritdoc(Cache)
    def get(self, k):
        return self.has(k)

    @inheritdoc(Cache)
    def put(self, k):
        evicted = None
        if not self.has(k):
            if len(self._cache) == self._maxlen:
                evicted_index = random.randint(0, self.maxlen-1)
                evicted = self.a[evicted_index]
                self.a[evicted_index] = k
                self._cache.remove(evicted)
            else:
                self.a[len(self._cache)] = k
            self._cache.add(k)
        return evicted
    
    @inheritdoc(Cache)
    def clear(self):
        self._cache.clear()

    
def set_rand_insert(cache, p, seed=None):
    """It modifies the instance of a cache object such that contents are
    inserted randomly instead of deterministically.
    
    This function modifies the behavior of the *put* method of a given cache
    instance such that it inserts contents randomly with a given probability
    
    Parameters
    ----------
    cache : Cache
        The instance of a cache to be applied random insertion
    p : float
        the insert probability
    seed : any hashable type, optional
        The seed of the random number generator
    """
    if not isinstance(cache, Cache):
        raise TypeError('cache must be an instance of Cache or its subclasses')
    if p < 0 or p > 1:
        raise ValueError('p must be a value between 0 and 1')
    random.seed(seed)
    put = cache.put
    def rand_put(k):
        if random.random() < p:
            return put(k)
    cache.put = rand_put
    return cache
