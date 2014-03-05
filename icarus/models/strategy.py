"""Implementations of all caching and routing strategies
"""
from __future__ import division
import random
import abc

import networkx as nx

from icarus.registry import register_strategy
from icarus.util import inheritdoc


__all__ = [
       'Strategy',
       'Hashrouting',
       'HashroutingSymmetric',
       'HashroutingAsymmetric',
       'HashroutingMulticast',
       'HashroutingHybridAM',
       'HashroutingHybridSM',
       'NoCache',
       'LeaveCopyEverywhere',
       'LeaveCopyDown',
       'CacheLessForMore',
       'RandomBernoulli',
       'RandomChoice'
           ]

#TODO: Implement BaseOnPath to reduce redundant code
#TODO: In Hashrouting, implement request routing phase under in single function

class Strategy(object):
    """
    Base strategy imported by all other strategy classes
    """
    
    __metaclass__ = abc.ABCMeta

    def __init__(self, view, controller, params=None):
        """Constructor
        
        Parameters
        ----------
        view : NetworkView
            An instance of the network view
        controller : NetworkController
            An instance of the network controller
        params : dict, optional
            A dict of additional strategy parameters
        """
        self.view = view
        self.controller = controller
        
    @abc.abstractmethod
    def process_event(self, time, receiver, content, log):
        """Process an event received from the simulation engine.
        
        This event is processed by executing relevant actions of the network
        controller, potentially based on the current status of the network
        retrieved from the network view.
        
        Parameters
        ----------
        time : int
            The timestamp of the event
        receiver : any hashable type
            The receiver node requesting a content
        content : any hashable type
            The content identifier requested by the receiver
        log : bool
            Indicates whether the event must be registered by the data
            collectors attached to the network.
        """
        raise NotImplementedError('The selected control plane must implement '
                                  'a process_event method')



class Hashrouting(Strategy):
    """Base class for all hash-routing implementations. Hash-routing
    implementations are described in [1]_.
        
    References
    ----------
    .. [1] L. Saino, I. Psaras and G. Pavlou, Hash-routing Schemes for
    Information-Centric Networking, in Proceedings of ACM SIGCOMM ICN'13
    workshop. Available:
    https://www.ee.ucl.ac.uk/~lsaino/publications/hashrouting-icn13.pdf
    
    """

    @inheritdoc(Strategy)
    def __init__(self, view, controller, params=None):
        super(Hashrouting, self).__init__(view, controller)
        cache_nodes = list(view.caches().keys())
        # Allocate results of hash function to caching nodes 
        self.cache_assignment = dict((i, cache_nodes[i]) 
                                      for i in range(len(cache_nodes)))

    def authoritative_cache(self, content):
        """Return the authoritative cache node for the given content
        
        Parameters
        ----------
        content : any hashable type
            The identifier of the content
            
        Returns
        -------
        authoritative_cache : any hashable type
            The node on which the authoritative cache is deployed
        """
        return self.cache_assignment[self.hash(content)]

    def hash(self, content):
        """Return a hash code of the content for hash-routing purposes
        
        
        Parameters
        ----------
        content : any hashable type
            The identifier of the content
            
        Returns
        -------
        hash : int
            The hash code of the content
        """
        #TODO: This hash function needs revision because it does not return
        # equally probably hash codes
        n = len(self.view.caches())
        h = content % n
        return h if (content/n) % 2 == 0 else (n - h - 1)


@register_strategy('HR_SYMM')
class HashroutingSymmetric(Hashrouting):
    """Hash-routing with symmetric routing (HR SYMM)
    """

    @inheritdoc(Strategy)
    def __init__(self, view, controller, params=None):
        super(HashroutingSymmetric, self).__init__(view, controller)

    @inheritdoc(Strategy)
    def process_event(self, time, receiver, content, log):
        # get all required data
        source = self.view.content_source(content)
        cache = self.authoritative_cache(content)
        # handle (and log if required) actual request
        self.controller.start_session(time, receiver, content, log)
        # Forward request to authoritative cache
        self.controller.forward_request_path(receiver, cache)
        if self.controller.get_content(cache):
            # We have a cache hit here
            self.controller.forward_content_path(cache, receiver)
        else:
            # Cache miss: go all the way to source
            self.controller.forward_request_path(cache, source)
            if not self.controller.get_content(source):
                raise RuntimeError('The content is not found the expected source')
            self.controller.forward_content_path(source, cache)
            # Insert in cache
            self.controller.put_content(cache)
            # Forward to receiver
            self.controller.forward_content_path(cache, receiver)
        self.controller.end_session()    


@register_strategy('HR_ASYMM')
class HashroutingAsymmetric(Hashrouting):
    """Hash-routing with asymmetric routing (HR ASYMM) 
    """

    @inheritdoc(Strategy)
    def __init__(self, view, controller, params=None):
        super(HashroutingAsymmetric, self).__init__(view, controller)
        
    @inheritdoc(Strategy)
    def process_event(self, time, receiver, content, log):
        # get all required data
        source = self.view.content_source(content)
        cache = self.authoritative_cache(content)
        # handle (and log if required) actual request
        self.controller.start_session(time, receiver, content, log)
        # Forward request to authoritative cache
        self.controller.forward_request_path(receiver, cache)
        if self.controller.get_content(cache):
            # We have a cache hit here
            self.controller.forward_content_path(cache, receiver)
        else:
            # Cache miss: go all the way to source
            self.controller.forward_request_path(cache, source)
            if not self.controller.get_content(source):
                raise RuntimeError('The content was not found at the expected source')   
            if cache in self.view.shortest_path(source, receiver):
                # Forward to cache
                self.controller.forward_content_path(source, cache)
                # Insert in cache
                self.controller.put_content(cache)
                # Forward to receiver
                self.controller.forward_content_path(cache, receiver)
            else:
                # Forward to receiver straight away
                self.controller.forward_content_path(source, receiver)
        self.controller.end_session()


@register_strategy('HR_MULTICAST')
class HashroutingMulticast(Hashrouting):
    """
    Hash-routing implementation with multicast delivery of content packets.
    
    In this strategy, if there is a cache miss, when contant packets return in
    the domain, the packet is multicast, one copy being sent to the
    authoritative cache and the other to the receiver. If the cache is on the
    path from source to receiver, this strategy behaves as a normal symmetric
    hash-routing strategy.
    """

    @inheritdoc(Strategy)
    def __init__(self, view, controller, params=None):
        super(HashroutingMulticast, self).__init__(view, controller)
        # map id of content to node with cache responsibility

    @inheritdoc(Strategy)
    def process_event(self, time, receiver, content, log):
        # get all required data
        source = self.view.content_source(content)
        cache = self.authoritative_cache(content)
        # handle (and log if required) actual request
        self.controller.start_session(time, receiver, content, log)
        # Forward request to authoritative cache
        self.controller.forward_request_path(receiver, cache)
        if self.controller.get_content(cache):
            # We have a cache hit here
            self.controller.forward_content_path(cache, receiver)
        else:
            # Cache miss: go all the way to source
            self.controller.forward_request_path(cache, source)
            if not self.controller.get_content(source):
                raise RuntimeError('The content is not found the expected source') 
            if cache in self.view.shortest_path(source, receiver):
                self.controller.forward_content_path(source, cache)
                # Insert in cache
                self.controller.put_content(cache)
                # Forward to receiver
                self.controller.forward_content_path(cache, receiver)
            else:
                # Multicast
                cache_path = self.view.shortest_path(source, cache)
                recv_path = self.view.shortest_path(source, receiver)
                
                # find what is the node that has to fork the content flow
                for i in range(1, min([len(cache_path), len(recv_path)])):
                    if cache_path[i] != recv_path[i]:
                        fork_node = cache_path[i-1]
                        break
                else: fork_node = cache
                self.controller.forward_content_path(source, fork_node)
                self.controller.forward_content_path(fork_node, receiver)
                self.controller.forward_content_path(fork_node, cache)
                self.controller.put_content(cache)
        self.controller.end_session()

        
        

@register_strategy('HR_HYBRID_AM')
class HashroutingHybridAM(Hashrouting):
    """
    Hash-routing implementation with hybrid asymmetric-multicast delivery of
    content packets.
    
    In this strategy, if there is a cache miss, when content packets return in
    the domain, the packet is delivered to the receiver following the shortest
    path. If the additional number of hops required to send a copy to the
    authoritative cache is below a specific fraction of the network diameter,
    then one copy is sent to the authoritative cache as well. If the cache is
    on the path from source to receiver, this strategy behaves as a normal
    symmetric hash-routing strategy.
    """

    @inheritdoc(Strategy)
    def __init__(self, view, controller, max_stretch=0.2):
        super(HashroutingHybridAM, self).__init__(view, controller)
        self.max_stretch = nx.diameter(view.topology()) * max_stretch

    @inheritdoc(Strategy)
    def process_event(self, time, receiver, content, log):
        # get all required data
        source = self.view.content_source(content)
        cache = self.authoritative_cache(content)
        # handle (and log if required) actual request
        self.controller.start_session(time, receiver, content, log)
        # Forward request to authoritative cache
        self.controller.forward_request_path(receiver, cache)
        if self.controller.get_content(cache):
            # We have a cache hit here
            self.controller.forward_content_path(cache, receiver)
        else:
            # Cache miss: go all the way to source
            self.controller.forward_request_path(cache, source)
            if not self.controller.get_content(source):
                raise RuntimeError('The content was not found at the expected source') 
            
            if cache in self.view.shortest_path(source, receiver):
                # Forward to cache
                self.controller.forward_content_path(source, cache)
                # Insert in cache
                self.controller.put_content(cache)
                # Forward to receiver
                self.controller.forward_content_path(cache, receiver)
            else:
                # Multicast
                cache_path = self.view.shortest_path(source, cache)
                recv_path = self.view.shortest_path(source, receiver)
                
                # find what is the node that has to fork the content flow
                for i in range(1, min([len(cache_path), len(recv_path)])):
                    if cache_path[i] != recv_path[i]:
                        fork_node = cache_path[i-1]
                        break
                else: fork_node = cache
                self.controller.forward_content_path(source, receiver)
                # multicast to cache only if stretch is under threshold
                if len(self.view.shortest_path(fork_node, cache)) - 1 < self.max_stretch:
                    self.controller.forward_content_path(fork_node, cache)
                    self.controller.put_content(cache)
        self.controller.end_session()
        

@register_strategy('HR_HYBRID_SM')
class HashroutingHybridSM(Hashrouting):
    """
    Hash-routing implementation with hybrid symmetric-multicast delivery of
    content packets.
    
    In this implementation, the edge router receiving a content packet decides
    whether to deliver the packet using multicast or symmetric hash-routing
    based on the total cost for delivering the Data to both cache and receiver
    in terms of hops.
    """

    @inheritdoc(Strategy)
    def __init__(self, view, controller, params=None):
        super(HashroutingHybridSM, self).__init__(view, controller)

    @inheritdoc(Strategy)
    def process_event(self, time, receiver, content, log):
        # get all required data
        source = self.view.content_source(content)
        cache = self.authoritative_cache(content)
        # handle (and log if required) actual request
        self.controller.start_session(time, receiver, content, log)
        # Forward request to authoritative cache
        self.controller.forward_request_path(receiver, cache)
        if self.controller.get_content(cache):
            # We have a cache hit here
            self.controller.forward_content_path(cache, receiver)
        else:
            # Cache miss: go all the way to source
            self.controller.forward_request_path(cache, source)
            if not self.controller.get_content(source):
                raise RuntimeError('The content is not found the expected source') 
            
            if cache in self.view.shortest_path(source, receiver):
                self.controller.forward_content_path(source, cache)
                # Insert in cache
                self.controller.put_content(cache)
                # Forward to receiver
                self.controller.forward_content_path(cache, receiver)
            else:
                # Multicast
                cache_path = self.view.shortest_path(source, cache)
                recv_path = self.view.shortest_path(source, receiver)
                
                # find what is the node that has to fork the content flow
                for i in range(1, min([len(cache_path), len(recv_path)])):
                    if cache_path[i] != recv_path[i]:
                        fork_node = cache_path[i-1]
                        break
                else: fork_node = cache
                
                symmetric_path_len = len(self.view.shortest_path(source, cache)) + \
                                     len(self.view.shortest_path(cache, receiver)) - 2
                multicast_path_len = len(self.view.shortest_path(source, fork_node)) + \
                                     len(self.view.shortest_path(fork_node, cache)) + \
                                     len(self.view.shortest_path(fork_node, receiver)) - 3
                
                self.controller.put_content(cache)
                # If symmetric and multicast have equal cost, choose symmetric
                # because of easier packet processing
                if symmetric_path_len <= multicast_path_len: # use symmetric delivery
                    # Symmetric delivery
                    self.controller.forward_content_path(source, cache)
                    self.controller.forward_content_path(cache, receiver)
                else:
                    # Multicast delivery
                    self.controller.forward_content_path(source, receiver)
                    self.controller.forward_content_path(fork_node, cache)
                self.controller.end_session()


@register_strategy('NO_CACHE')
class NoCache(Strategy):
    """Strategy without any caching
    
    This corresponds to the traffic in a normal TCP/IP network without any
    CDNs or overlay caching, where all content requests are served by the 
    original source.
    """

    @inheritdoc(Strategy)
    def __init__(self, view, controller, symm_paths=True, params=None):
        super(NoCache, self).__init__(view, controller)
        self.symm_paths = symm_paths
    
    @inheritdoc(Strategy)
    def process_event(self, time, receiver, content, log):
        # get all required data
        source = self.view.content_source(content)
        path = self.view.shortest_path(receiver, source)
        # Route requests to original source
        self.controller.start_session(time, receiver, content, log)
        self.controller.forward_request_path(receiver, source)
        self.controller.get_content(source)
        # Route content back to receiver
        path = list(reversed(path)) if self.symm_paths \
                        else self.view.shortest_path(source, receiver)
        self.controller.forward_content_path(source, receiver)
        self.controller.end_session()



@register_strategy('LCE')
class LeaveCopyEverywhere(Strategy):
    """Leave Copy Everywhere (LCE) strategy.
    
    In this strategy a copy of a content is replicated at any cache on the
    path between serving node and receiver.
    """

    @inheritdoc(Strategy)
    def __init__(self, view, controller, symm_paths=True):
        super(LeaveCopyEverywhere, self).__init__(view, controller)
        self.symm_paths = symm_paths

    @inheritdoc(Strategy)
    def process_event(self, time, receiver, content, log):
        # get all required data
        source = self.view.content_source(content)
        path = self.view.shortest_path(receiver, source)
        # Route requests to original source and queries caches on the path
        self.controller.start_session(time, receiver, content, log)
        for hop in range(1, len(path)):
            u = path[hop - 1]
            v = path[hop]
            self.controller.forward_request_hop(u, v)
            if v in self.view.caches():
                if self.controller.get_content(v):
                    serving_node = v
                    break
            # No cache hits, get content from source
            self.controller.get_content(v)
            serving_node = v
        # Return content
        path = list(reversed(path[:hop + 1])) if self.symm_paths \
                        else self.view.shortest_path(serving_node, receiver)
        for hop in range(1, len(path)):
            u = path[hop - 1]
            v = path[hop]
            self.controller.forward_content_hop(u, v)
            if v in self.view.caches():
                # insert content
                self.controller.put_content(v)
        self.controller.end_session()


@register_strategy('LCD')
class LeaveCopyDown(Strategy):
    """Leave Copy Down (LCD) strategy.
    
    According to this strategy, one copy of a content is replicated only in
    the caching node you hop away from the serving node in the direction of
    the receiver. This strategy is described in [2]_.
    
    Rereferences
    ------------
    ..[2] N. Laoutaris, H. Che, i. Stavrakakis, The LCD interconnection of LRU
          caches and its analysis. 
          Available: http://cs-people.bu.edu/nlaout/analysis_PEVA.pdf 
    """

    @inheritdoc(Strategy)
    def __init__(self, view, controller, symm_paths=True):
        super(LeaveCopyDown, self).__init__(view, controller)
        self.symm_paths = symm_paths

    @inheritdoc(Strategy)
    def process_event(self, time, receiver, content, log):
        # get all required data
        source = self.view.content_source(content)
        path = self.view.shortest_path(receiver, source)
        # Route requests to original source and queries caches on the path
        self.controller.start_session(time, receiver, content, log)
        for hop in range(1, len(path)):
            u = path[hop - 1]
            v = path[hop]
            self.controller.forward_request_hop(u, v)
            if v in self.view.caches():
                if self.controller.get_content(v):
                    serving_node = v
                    break
            # No cache hits, get content from source
            self.controller.get_content(v)
            serving_node = v
        # Return content
        path = list(reversed(path[:hop + 1])) if self.symm_paths \
                        else self.view.shortest_path(serving_node, receiver)
        # Leave a copy of the content only in the cache one level down the hit
        # caching node
        copied = False
        for hop in range(1, len(path)):
            u = path[hop - 1]
            v = path[hop]
            self.controller.forward_content_hop(u, v)
            if not copied and v != receiver and v in self.view.caches():
                self.controller.put_content(v)
                copied = True
        self.controller.end_session()


@register_strategy('PROB_CACHE')
class ProbCache(Strategy):
    """ProbCache strategy [3]_
    
    
    References
    ----------
    ..[3] I. Psaras, W. Chai, G. Pavlou, Probabilistic In-Network Caching for
          Information-Centric Networks, in Proc. of ACM SIGCOMM ICN '12
          Available: http://www.ee.ucl.ac.uk/~uceeips/prob-cache-icn-sigcomm12.pdf
    """

    @inheritdoc(Strategy)
    def __init__(self, view, controller, symm_paths= True, t_tw=10):
        super(ProbCache, self).__init__(view, controller)
        self.symm_paths = symm_paths
        self.t_tw = t_tw
        self.cache_size = self.view.caches()
    
    @inheritdoc(Strategy)
    def process_event(self, time, receiver, content, log):
        # get all required data
        source = self.view.content_source(content)
        path = self.view.shortest_path(receiver, source)
        # Route requests to original source and queries caches on the path
        self.controller.start_session(time, receiver, content, log)
        for hop in range(1, len(path)):
            u = path[hop - 1]
            v = path[hop]
            self.controller.forward_request_hop(u, v)
            if v in self.view.caches():
                if self.controller.get_content(v):
                    serving_node = v
                    break
            # No cache hits, get content from source
            self.controller.get_content(v)
            serving_node = v
        # Return content
        path = list(reversed(path[:hop + 1])) if self.symm_paths \
                        else self.view.shortest_path(serving_node, receiver)
        c = len(path) - 1.0
        x = 0.0
        for hop in range(1, len(path)):
            u = path[hop - 1]
            v = path[hop]    
            N = sum([self.cache_size[n] for n in path[hop - 1:]
                     if n in self.cache_size])
            if v in self.cache_size:
                x += 1
            self.controller.forward_content_hop(u, v)
            if v != receiver and v in self.cache_size:
                prob_cache = float(N)/(self.t_tw * self.cache_size[v])*(x/c)**c
                if random.random() < prob_cache:
                    self.controller.put_content(v)
        self.controller.end_session()


@register_strategy('CL4M')
class CacheLessForMore(Strategy):
    """Cache less for more strategy [4]_.
    
    References
    ----------
    ..[4] W. Chai, D. He, I. Psaras, G. Pavlou, Cache Less for More in
          Information-centric Networks, in IFIP NETWORKING '12
          Available: http://www.ee.ucl.ac.uk/~uceeips/centrality-networking12.pdf
    """

    @inheritdoc(Strategy)
    def __init__(self, view, controller, symm_paths=True, use_ego_betw=False):
        super(CacheLessForMore, self).__init__(view, controller)
        self.symm_paths = symm_paths
        topology = view.topology()
        if use_ego_betw:
            self.betw = dict((v, nx.betweenness_centrality(nx.ego_graph(topology, v))[v])
                             for v in topology.nodes_iter())
        else:
            self.betw = nx.betweenness_centrality(topology)
    
    @inheritdoc(Strategy)
    def process_event(self, time, receiver, content, log):
        # get all required data
        source = self.view.content_source(content)
        path = self.view.shortest_path(receiver, source)
        # Route requests to original source and queries caches on the path
        self.controller.start_session(time, receiver, content, log)
        for hop in range(1, len(path)):
            u = path[hop - 1]
            v = path[hop]
            self.controller.forward_request_hop(u, v)
            if v in self.view.caches():
                if self.controller.get_content(v):
                    serving_node = v
                    break
            # No cache hits, get content from source
            self.controller.get_content(v)
            serving_node = v
        # Return content
        path = list(reversed(path[:hop + 1])) if self.symm_paths \
                        else self.view.shortest_path(serving_node, receiver)
        # get the cache with maximum betweenness centrality
        # if there are more than one cache with max betw then pick the one
        # closer to the receiver
        max_betw = -1
        designated_cache = None
        for v in path[1:]:
            if v in self.view.caches():
                if self.betw[v] >= max_betw:
                    max_betw = self.betw[v]
                    designated_cache = v
        # Forward content
        for hop in range(1, len(path)):
            u = path[hop - 1]
            v = path[hop]
            self.controller.forward_content_hop(u, v)
            if v == designated_cache:
                self.controller.put_content(v)
        self.controller.end_session()  
        
        

@register_strategy('RAND_BERNOULLI')
class RandomBernoulli(Strategy):
    """Bernoulli random cache insertion.
    
    In this strategy, a content is randomly inserted in a cache on the path
    from serving node to receiver with probability *p*.
    """

    @inheritdoc(Strategy)
    def __init__(self, view, controller, symm_paths=True, p=0.2):
        super(RandomBernoulli, self).__init__(view, controller)
        self.symm_paths = symm_paths
        self.p = p
    
    @inheritdoc(Strategy)
    def process_event(self, time, receiver, content, log):
        # get all required data
        source = self.view.content_source(content)
        path = self.view.shortest_path(receiver, source)
        # Route requests to original source and queries caches on the path
        self.controller.start_session(time, receiver, content, log)
        for hop in range(1, len(path)):
            u = path[hop - 1]
            v = path[hop]
            self.controller.forward_request_hop(u, v)
            if v in self.view.caches():
                if self.controller.get_content(v):
                    serving_node = v
                    break
            # No cache hits, get content from source
            self.controller.get_content(v)
            serving_node = v
        # Return content
        path = list(reversed(path[:hop + 1])) if self.symm_paths \
                        else self.view.shortest_path(serving_node, receiver)
        for hop in range(1, len(path)):
            u = path[hop - 1]
            v = path[hop]
            self.controller.forward_content_hop(u, v)
            if v != receiver and v not in self.view.caches():
                if random.random() < self.p:
                    self.controller.put_content(v)
        self.controller.end_session()

@register_strategy('RAND_CHOICE')
class RandomChoice(Strategy):
    """Random choice strategy
    
    This strategy stores the served content exactly in one single cache on the
    path from serving node to receiver selected randomly.
    """

    @inheritdoc(Strategy)
    def __init__(self, view, controller, symm_paths=True, params=None):
        super(RandomChoice, self).__init__(view, controller)
        self.symm_paths = symm_paths
    
    @inheritdoc(Strategy)
    def process_event(self, time, receiver, content, log):
        # get all required data
        source = self.view.content_source(content)
        path = self.view.shortest_path(receiver, source)
        # Route requests to original source and queries caches on the path
        self.controller.start_session(time, receiver, content, log)
        for hop in range(1, len(path)):
            u = path[hop - 1]
            v = path[hop]
            self.controller.forward_request_hop(u, v)
            if v in self.view.caches():
                if self.controller.get_content(v):
                    serving_node = v
                    break
            # No cache hits, get content from source
            self.controller.get_content(v)
            serving_node = v
        # Return content
        path = list(reversed(path[:hop + 1])) if self.symm_paths \
                        else self.view.shortest_path(serving_node, receiver)
        caches = [v for v in path[1:-1] if v in self.view.caches()]
        designated_cache = random.choice(caches) if len(caches) > 0 else None
        for hop in range(1, len(path)):
            u = path[hop - 1]
            v = path[hop]
            self.controller.forward_content_hop(u, v)
            if v == designated_cache:
                self.controller.put_content(v)
        self.controller.end_session() 

            