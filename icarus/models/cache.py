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
        'LruCache'
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
