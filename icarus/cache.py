"""Cache implementation
"""
from collections import deque

class Cache(object):
    """
    Implementation of cache with LRU eviction policy
    """
    
    def __init__(self, max_size):
        """
        Constructor
        """
        self.cache = deque(maxlen=int(max_size))
    
    def store(self, content):
        """
        Stores the content ID in the cache if not present yet. Otherwise, it
        pushes it on top of the cache 
        """
        if not self.has_content(content):
            self.cache.appendleft(content)

    def has_content(self, content):
        """
        Return True if the cache contains the piece of content (and updates its
        internal status, e.g. push content on top of LRU stack) otherwise
        returns False
        """
        # search content over the list
        # if it has it push on top, otherwise return false
        try:
            self.cache.remove(content)
            self.cache.appendleft(content)
        except ValueError:
            return False
        return True

