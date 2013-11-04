"""
Implementations of all the cache strategies off-path and on-path
"""
import networkx as nx
import random
from os import path
from fnss import get_stack
from icarus.cache import Cache
from icarus.logging import LinkLogger, CacheLogger, DelayLogger, StretchLogger, \
    NetworkLoadSummary, CacheHitRatioSummary, \
    PACKET_TYPE_INTEREST, PACKET_TYPE_DATA, \
    EVENT_CACHE_HIT, EVENT_SERVER_HIT


class BaseStrategy(object):
    """
    Base strategy imported by all other strategy classes
    """

    def __init__(self, topology, log_dir, scenario_id):
        """
        Constructor
        """
        # create logging objects
        # for running on clay or EE lab, open logging files in /tmp
        # and then (compress it) and move it to home. This is to avoid frequent
        # NFS writes, so I write on tmp which is on local drive and copy to home
        # (NFS) only when the simulation is over.
        # Compression may be needed on EE lab machine because there is a 5 GB
        # quota that might be exceeded by logs
        self.log_dir = log_dir
        self.scenario_id = scenario_id
        self.link_logger = LinkLogger(path.join(log_dir, 'RESULTS_%s_LINK.txt' % scenario_id))
        self.cache_logger = CacheLogger(path.join(log_dir, 'RESULTS_%s_CACHE.txt' % scenario_id))
        self.delay_logger = DelayLogger(path.join(log_dir, 'RESULTS_%s_DELAY.txt' % scenario_id))
        self.topology = topology
        # calc shortest paths
        self.shortest_path = nx.all_pairs_dijkstra_path(topology, weight='weight')
        # get location of caches and content sources
        self.content_location = {}   # dict of location of contents keyed by content ID
        self.cache_size = {}         # dict of cache sizes keyed by node
        # Link type: internal or external
        self.link_type = dict([((u,v), topology.edge[u][v]['type'])
                               for u in topology.edge
                               for v in topology.edge[u]])
        for node in topology.nodes_iter():
            stack_name, stack_props = get_stack(topology, node)
            if stack_name == 'cache':
                self.cache_size[node] = stack_props['size']
            elif stack_name == 'source':
                contents = stack_props['contents']
                for content in contents:
                    self.content_location[content] = node
        # create actual cache objects
        self.caches = dict([(node, Cache(self.cache_size[node])) for node in self.cache_size])

    def log_transfer(self, time, origin_node, destination_node, packet_type, content_id):
        """
        Log the transfer of a packet from an origin to a destination node.
        It is assumed that routing is based on Dijkstra shortest paths.
        """
        path = self.shortest_path[origin_node][destination_node]
        for hop in range(1, len(path)):
            u = path[hop - 1]
            v = path[hop]
            self.link_logger.log_link_info(time, u, v, packet_type, content_id, self.link_type[(u,v)])

    def content_hash(self, content_id):
        """
        Return a hash code of the content ID for hash-routing purposes
        """
        #TODO: This hash function needs revision cause it does not return equally probably hash codes
        n_caches = len(self.cache_size)
        hash_code = content_id % n_caches
        if (content_id/n_caches) % 2 == 0:
            return hash_code
        else:
            return n_caches - hash_code - 1
    
    
    def assign_caches(self, topology, cache_size, replicas, **kwargs):
        """
        Algorithm that decides how to allocate intervals of hash
        space to various caches.
        
        It returns a dictionary of lists keyed by hash interval ID. Each list is
        the list of the caches that are authorized to store the content. A list is
        returned also in the case the number of replicas is 1.
        """
        cache_nodes = list(cache_size.keys())
        return dict([(i, cache_nodes[i]) for i in range(len(cache_size))])
        
    def close(self):
        # Add entry to summary log file
        CacheHitRatioSummary(self.log_dir).write_summary(self.scenario_id, self.cache_logger.cache_hit_ratio())
        NetworkLoadSummary(self.log_dir).write_summary(self.scenario_id, self.link_logger.network_load())
        # Copy files back in my home folder before exiting
        self.link_logger.close()
        self.cache_logger.close()
        self.delay_logger.close()


class NoCache(BaseStrategy):
    """Strategy without any caching
    """

    def __init__(self, topology, log_dir, scenario_id, params=None):
        '''
        Constructor
        '''
        super(NoCache, self).__init__(topology, log_dir, scenario_id)
    
    def handle_event(self, time, event):
        receiver = event['receiver']
        content = event['content']
        log = event['log']
        
        source = self.content_location[content]
        if log:
            req_delay = 0
            resp_delay = 0
            
            # Log request path
            path = self.shortest_path[receiver][source]
            for hop in range(1, len(path)):
                u = path[hop - 1]
                v = path[hop]
                req_delay += self.topology.edge[u][v]['delay']
            self.link_logger.log_link_info(time, u, v, PACKET_TYPE_INTEREST, content, self.link_type[(u,v)])
            
            # Log response path
            path = self.shortest_path[source][receiver]
            for hop in range(1, len(path)):
                u = path[hop - 1]
                v = path[hop]
                resp_delay += self.topology.edge[u][v]['delay']
            self.link_logger.log_link_info(time, u, v, PACKET_TYPE_DATA, content, self.link_type[(u,v)])

            # Log delay of request and response
            self.delay_logger.log_delay_info(time, receiver, source, content, req_delay, resp_delay)



class HashrouteSymmetric(BaseStrategy):
    """Hashroute with symmetric routing
    """

    def __init__(self, topology, log_dir, scenario_id, params=None):
        '''
        Constructor
        '''
        super(HashrouteSymmetric, self).__init__(topology, log_dir, scenario_id)
        # map id of content to node with cache responsibility
        self.cache_assignment = self.assign_caches(topology, self.cache_size, replicas=1)
        self.stretch_logger = StretchLogger(path.join(log_dir, 'RESULTS_%s_STRETCH.txt' % scenario_id))
    
    def handle_event(self, time, event):
        # get all required data
        receiver = event['receiver']
        content = event['content']
        log = event['log']
        source = self.content_location[content]
        cache = self.cache_assignment[self.content_hash(content)]
        # handle (and log if required) actual request
        if log: self.log_transfer(time, receiver, cache, PACKET_TYPE_INTEREST, content)
        has_content = self.caches[cache].has_content(content)
        if has_content and log:
            self.cache_logger.log_cache_info(time, EVENT_CACHE_HIT, content, receiver, cache, source)
            self.log_transfer(time, cache, receiver, PACKET_TYPE_DATA, content)
            return
        else:
            if log:
                self.log_transfer(time, cache, source, PACKET_TYPE_INTEREST, content)
                self.cache_logger.log_cache_info(time, EVENT_SERVER_HIT, content, receiver, cache, source)
                self.log_transfer(time, source, cache, PACKET_TYPE_DATA, content) # pass via cache
                self.log_transfer(time, cache, receiver, PACKET_TYPE_DATA, content)
                optimal_path_len = len(self.shortest_path[source][receiver]) - 1
                actual_path_len = len(self.shortest_path[source][cache]) + len(self.shortest_path[cache][receiver]) - 2 
                self.stretch_logger.log_stretch_info(time, receiver, source, content, optimal_path_len, actual_path_len)
            self.caches[cache].store(content) # insert content
            return
    
    def close(self):
        super(HashrouteSymmetric, self).close()
        self.stretch_logger.close()



class HashrouteAsymmetric(BaseStrategy):

    def __init__(self, topology, log_dir, scenario_id, params=None):
        '''
        Constructor
        '''
        super(HashrouteAsymmetric, self).__init__(topology, log_dir, scenario_id)
        # map id of content to node with cache responsibility
        self.cache_assignment = self.assign_caches(topology, self.cache_size, replicas=1)
        
    
    def handle_event(self, time, event):
        # get all required data
        receiver = event['receiver']
        content = event['content']
        log = event['log']
        source = self.content_location[content]
        cache = self.cache_assignment[self.content_hash(content)]
        # handle (and log if required) actual request
        if log: self.log_transfer(time, receiver, cache, PACKET_TYPE_INTEREST, content)
        has_content = self.caches[cache].has_content(content)
        if has_content and log:
            self.cache_logger.log_cache_info(time, EVENT_CACHE_HIT, content, receiver, cache, source)
            self.log_transfer(time, cache, receiver, PACKET_TYPE_DATA, content)
            return
        else:
            if log:
                self.log_transfer(time, cache, source, PACKET_TYPE_INTEREST, content)
                self.cache_logger.log_cache_info(time, EVENT_SERVER_HIT, content, receiver, cache, source)
            if cache in self.shortest_path[source][receiver]:
                self.caches[cache].store(content) # insert content
                if log:
                    self.log_transfer(time, source, cache, PACKET_TYPE_DATA, content)
                    self.log_transfer(time, cache, receiver, PACKET_TYPE_DATA, content)
                return
            else:
                if log: self.log_transfer(time, source, receiver, PACKET_TYPE_DATA, content)
                return


class HashrouteMulticast(BaseStrategy):
    """
    Hashroute implementation with multicast delivery of Data packets.
    
    In this strategy, if there is a cache miss, when DATA packets returns in
    the domain, the packet is multicasted, one copy being sent to the
    authoritative cache and the other to the receiver. If the cache is on the
    path from source to receiver, this strategy behaves as a normal asymmetric
    HashRoute
    """

    def __init__(self, topology, log_dir, scenario_id, params=None):
        '''
        Constructor
        '''
        super(HashrouteMulticast, self).__init__(topology, log_dir, scenario_id)
        # map id of content to node with cache responsibility
        self.cache_assignment = self.assign_caches(topology, self.cache_size, replicas=1)
        self.stretch_logger = StretchLogger(path.join(log_dir, 'RESULTS_%s_STRETCH.txt' % scenario_id))

    
    def handle_event(self, time, event):
        # get all required data
        receiver = event['receiver']
        content = event['content']
        log = event['log']
        source = self.content_location[content]
        cache = self.cache_assignment[self.content_hash(content)]
        # handle (and log if required) actual request 
        if log: self.log_transfer(time, receiver, cache, PACKET_TYPE_INTEREST, content)
        has_content = self.caches[cache].has_content(content)
        if has_content and log:
            self.cache_logger.log_cache_info(time, EVENT_CACHE_HIT, content, receiver, cache, source)
            self.log_transfer(time, cache, receiver, PACKET_TYPE_DATA, content)
        else:
            if log:
                self.log_transfer(time, cache, source, PACKET_TYPE_INTEREST, content)
                self.cache_logger.log_cache_info(time, EVENT_SERVER_HIT, content, receiver, cache, source)
            if cache in self.shortest_path[source][receiver]:
                self.caches[cache].store(content) # insert content
                if log:
                    self.log_transfer(time, source, cache, PACKET_TYPE_DATA, content) # pass via cache
                    self.log_transfer(time, cache, receiver, PACKET_TYPE_DATA, content) # pass via cache
                    path_len = len(self.shortest_path[source][receiver])
                    self.stretch_logger.log_stretch_info(time, receiver, source, content, path_len, path_len)
                return
            else:
                #do multicast here
                cache_path = self.shortest_path[source][cache]
                recv_path = self.shortest_path[source][receiver]
                
                # find what is the node that has to fork the DATA packet
                for i in range(1, min([len(cache_path), len(recv_path)])):
                    if cache_path[i] != recv_path[i]:
                        fork_node = cache_path[i-1]
                        break
                else: fork_node = cache
                if log:
                    self.log_transfer(time, source, fork_node, PACKET_TYPE_DATA, content)
                    self.log_transfer(time, fork_node, cache, PACKET_TYPE_DATA, content)
                    self.log_transfer(time, fork_node, receiver, PACKET_TYPE_DATA, content)
                    optimal_path_len = len(self.shortest_path[source][receiver]) - 1
                    actual_path_len = len(self.shortest_path[source][fork_node]) + \
                                      len(self.shortest_path[fork_node][cache]) + \
                                      len(self.shortest_path[fork_node][receiver]) - 3
                    self.stretch_logger.log_stretch_info(time, receiver, source, content, optimal_path_len, actual_path_len)
                self.caches[cache].store(content)
                return

    def close(self):
        super(HashrouteMulticast, self).close()
        self.stretch_logger.close()
        
        


class HashrouteHybridStretch(BaseStrategy):
    """
    Hashroute implementation with hybrid delivery of Data packets.
    
    In this strategy, if there is a cache miss, when DATA packets returns in
    the domain, the packet is multicasted, one copy being sent to the
    authoritative cache and the other to the receiver. If the cache is on the
    path from source to receiver, this strategy behaves as a normal asymmetric
    HashRoute
    """

    def __init__(self, topology, log_dir, scenario_id, params=None):
        '''
        Constructor
        '''
        super(HashrouteHybridStretch, self).__init__(topology, log_dir, scenario_id)
        # map id of content to node with cache responsibility
        params = {'max_stretch': 0.2}
        self.cache_assignment = self.assign_caches(topology, self.cache_size, replicas=1)
        self.max_stretch = nx.diameter(topology) * params['max_stretch']
        self.stretch_logger = StretchLogger(path.join(log_dir, 'RESULTS_%s_STRETCH.txt' % scenario_id))

    
    def handle_event(self, time, event):
        # get all required data
        receiver = event['receiver']
        content = event['content']
        log = event['log']
        source = self.content_location[content]
        cache = self.cache_assignment[self.content_hash(content)]
        # handle (and log if required) actual request 
        if log: self.log_transfer(time, receiver, cache, PACKET_TYPE_INTEREST, content)
        has_content = self.caches[cache].has_content(content)
        if has_content and log:
            self.cache_logger.log_cache_info(time, EVENT_CACHE_HIT, content, receiver, cache, source)
            self.log_transfer(time, cache, receiver, PACKET_TYPE_DATA, content)
        else:
            if log:
                self.log_transfer(time, cache, source, PACKET_TYPE_INTEREST, content)
                self.cache_logger.log_cache_info(time, EVENT_SERVER_HIT, content, receiver, cache, source)
            if cache in self.shortest_path[source][receiver]:
                self.caches[cache].store(content) # insert content
                if log:
                    self.log_transfer(time, source, cache, PACKET_TYPE_DATA, content) # pass via cache
                    self.log_transfer(time, cache, receiver, PACKET_TYPE_DATA, content) # pass via cache
                    path_len = len(self.shortest_path[source][receiver])
                    self.stretch_logger.log_stretch_info(time, receiver, source, content, path_len, path_len)
                return
            else:
                #do multicast here
                cache_path = self.shortest_path[source][cache]
                recv_path = self.shortest_path[source][receiver]
                
                # find what is the node that has to fork the DATA packet
                for i in range(1, min([len(cache_path), len(recv_path)])):
                    if cache_path[i] != recv_path[i]:
                        fork_node = cache_path[i-1]
                        break
                else: fork_node = cache
                optimal_path_len = len(self.shortest_path[source][receiver]) - 1
                actual_path_len = len(self.shortest_path[source][fork_node]) + \
                                  len(self.shortest_path[fork_node][cache]) + \
                                  len(self.shortest_path[fork_node][receiver]) - 3
                # multicast to cache only if stretch is under threshold
                go_to_cache = ((actual_path_len - optimal_path_len) < self.max_stretch)
                if go_to_cache:
                    self.caches[cache].store(content)
                if log:
                    self.log_transfer(time, source, fork_node, PACKET_TYPE_DATA, content)
                    self.log_transfer(time, fork_node, receiver, PACKET_TYPE_DATA, content)
                    if go_to_cache:
                        self.log_transfer(time, fork_node, cache, PACKET_TYPE_DATA, content)
                        self.stretch_logger.log_stretch_info(time, receiver, source, content, optimal_path_len, actual_path_len)

    def close(self):
        super(HashrouteHybridStretch, self).close()
        self.stretch_logger.close()






class HashrouteHybridSymmMCast(BaseStrategy):
    """
    Hashroute implementation with hybrid delivery of Data packets.
    
    In this implementation, the edge router receiving a DATA packet decides
    whether to deliver the packet using Multicast or asymmetric hashroute
    based on the total cost for delivering the Data to both cache and receiver
    in terms of hops.
    """

    def __init__(self, topology, log_dir, scenario_id, params=None):
        '''
        Constructor
        '''
        super(HashrouteHybridSymmMCast, self).__init__(topology, log_dir, scenario_id)
        # map id of content to node with cache responsibility
        self.cache_assignment = self.assign_caches(topology, self.cache_size, replicas=1)
        self.stretch_logger = StretchLogger(path.join(log_dir, 'RESULTS_%s_STRETCH.txt' % scenario_id))
        self.scenario_id = scenario_id
        self.symm_count = 0
        self.mcast_count = 0

    
    def handle_event(self, time, event):
        # get all required data
        receiver = event['receiver']
        content = event['content']
        log = event['log']
        source = self.content_location[content]
        cache = self.cache_assignment[self.content_hash(content)]
        # handle (and log if required) actual request 
        if log: self.log_transfer(time, receiver, cache, PACKET_TYPE_INTEREST, content)
        has_content = self.caches[cache].has_content(content)
        if has_content and log:
            self.cache_logger.log_cache_info(time, EVENT_CACHE_HIT, content, receiver, cache, source)
            self.log_transfer(time, cache, receiver, PACKET_TYPE_DATA, content)
        else:
            if log:
                self.log_transfer(time, cache, source, PACKET_TYPE_INTEREST, content)
                self.cache_logger.log_cache_info(time, EVENT_SERVER_HIT, content, receiver, cache, source)
            if cache in self.shortest_path[source][receiver]:
                self.caches[cache].store(content) # insert content
                if log:
                    self.log_transfer(time, source, cache, PACKET_TYPE_DATA, content) # pass via cache
                    self.log_transfer(time, cache, receiver, PACKET_TYPE_DATA, content) # pass via cache
                    path_len = len(self.shortest_path[source][receiver])
                    self.stretch_logger.log_stretch_info(time, receiver, source, content, path_len, path_len)
                return
            else:
                #do multicast here
                cache_path = self.shortest_path[source][cache]
                recv_path = self.shortest_path[source][receiver]
                
                # find what is the node that has to fork the DATA packet
                for i in range(1, min([len(cache_path), len(recv_path)])):
                    if cache_path[i] != recv_path[i]:
                        fork_node = cache_path[i-1]
                        break
                else: fork_node = cache
                
                optimal_path_len   = len(self.shortest_path[source][receiver])
                symmetric_path_len = len(self.shortest_path[source][cache]) + \
                                     len(self.shortest_path[cache][receiver]) - 2
                multicast_path_len = len(self.shortest_path[source][fork_node]) + \
                                     len(self.shortest_path[fork_node][cache]) + \
                                     len(self.shortest_path[fork_node][receiver]) - 3
                # insert content in cache
                self.caches[cache].store(content)
                # decide if use symmetric or multicast depending on total costs
                if symmetric_path_len < multicast_path_len: # use symmetric delivery
                    if log:
                        self.symm_count += 1
                        self.log_transfer(time, source, cache, PACKET_TYPE_DATA, content)
                        self.log_transfer(time, cache, receiver, PACKET_TYPE_DATA, content)
                        self.stretch_logger.log_stretch_info(time, receiver, source, content, optimal_path_len, symmetric_path_len)
                else: # use multicast delivery
                    if log:
                        self.mcast_count += 1
                        self.log_transfer(time, source, fork_node, PACKET_TYPE_DATA, content)
                        self.log_transfer(time, fork_node, receiver, PACKET_TYPE_DATA, content)
                        self.log_transfer(time, fork_node, cache, PACKET_TYPE_DATA, content)
                        self.stretch_logger.log_stretch_info(time, receiver, source, content, optimal_path_len, multicast_path_len)
             

    def close(self):
        super(HashrouteHybridSymmMCast, self).close()
        self.stretch_logger.close()






class CeeLru(BaseStrategy):
    """
    Cache Everything Everywhere with LRU eviction
    """

    def __init__(self, topology, log_dir, scenario_id, params=None):
        """
        Constructor
        """
        super(CeeLru, self).__init__(topology, log_dir, scenario_id)

    def handle_event(self, time, event):
        # get all required data
        receiver = event['receiver']
        content = event['content']
        log = event['log']
        source = self.content_location[content]
        path = self.shortest_path[receiver][source]
        # handle (and log if required) actual request
        req_delay = 0
        resp_delay = 0
        for hop in range(1, len(path)):
            u = path[hop - 1]
            v = path[hop]
            if log:
                self.link_logger.log_link_info(time, u, v, PACKET_TYPE_INTEREST, content, self.link_type[(u,v)])
                req_delay += self.topology.edge[u][v]['delay']
            if v == source:
                if log: self.cache_logger.log_cache_info(time, EVENT_SERVER_HIT, content, receiver, 'N/A', source)
                serving_node = v
                break
            if get_stack(self.topology, v)[0] == 'cache':
                if self.caches[v].has_content(content):
                    if log: self.cache_logger.log_cache_info(time, EVENT_CACHE_HIT, content, receiver, v, source)
                    serving_node = v
                    break
        path = self.shortest_path[serving_node][receiver]
        for hop in range(1, len(path)):
            u = path[hop - 1]
            v = path[hop]
            if log:
                self.link_logger.log_link_info(time, u, v, PACKET_TYPE_DATA, content, self.link_type[(u,v)])
                resp_delay += self.topology.edge[u][v]['delay']
            if v != receiver and get_stack(self.topology, v)[0] == 'cache':
                self.caches[v].store(content) # insert content
        if log:
            self.delay_logger.log_delay_info(time, receiver, source, content, req_delay, resp_delay)



class ProbCache(BaseStrategy):
    """
    ProbCache implementation
    
    I. Psaras et al, Probabilistic In-Network Caching for Information-Centric Networks, ACM SIGCOMM ICN '12
    http://www.ee.ucl.ac.uk/~uceeips/prob-cache-icn-sigcomm12.pdf
    """

    def __init__(self, topology, log_dir, scenario_id, params=None):
        # TODO: Add t_tw to params
        super(ProbCache, self).__init__(topology, log_dir, scenario_id)
        self.t_tw = 10
    
    def handle_event(self, time, event):
        # get all required data
        receiver = event['receiver']
        content = event['content']
        log = event['log']
        source = self.content_location[content]
        path = self.shortest_path[receiver][source]
        # handle (and log if required) actual request 
        for hop in range(1, len(path)):
            u = path[hop - 1]
            v = path[hop]
            if log: self.link_logger.log_link_info(time, u, v, PACKET_TYPE_INTEREST, content, self.link_type[(u,v)])
            if v == source:
                if log: self.cache_logger.log_cache_info(time, EVENT_SERVER_HIT, content, receiver, 'N/A', source)
                serving_node = v
                break
            if get_stack(self.topology, v)[0] == 'cache':
                if self.caches[v].has_content(content):
                    if log: self.cache_logger.log_cache_info(time, EVENT_CACHE_HIT, content, receiver, v, source)
                    serving_node = v
                    break
        path = self.shortest_path[serving_node][receiver]
        c = len(path) - 1
        N = sum([self.cache_size[v] for v in path if get_stack(self.topology, v)[0] == 'cache'])
        x = 0
        for hop in range(1, len(path)):
            u = path[hop - 1]
            v = path[hop]
            if get_stack(self.topology, v)[0] == 'cache':
                x += 1
            if log: self.link_logger.log_link_info(time, u, v, PACKET_TYPE_DATA, content, self.link_type[(u,v)])
            if v != receiver and get_stack(self.topology, v)[0] == 'cache':
                prob_cache = float(N)/(self.t_tw * self.cache_size[v]) * (float(x)/float(c))**c
                if random.random() < prob_cache:
                    self.caches[v].store(content) # insert content


class Cl4m(BaseStrategy):
    """Cache less for more implementation
    
    W. Chai et al., Cache Less for More in Information-centric Networks, IFIP NETWORKING '12
    http://www.ee.ucl.ac.uk/~uceeips/centrality-networking12.pdf
    """

    def __init__(self, topology, log_dir, scenario_id, params=None):
        """
        Constructor
        """
        super(Cl4m, self).__init__(topology, log_dir, scenario_id)
        self.betw = nx.betweenness_centrality(topology)
    
    def handle_event(self, time, event):
        """
        Handle request
        """
        # get all required data
        receiver = event['receiver']
        content = event['content']
        log = event['log']
        source = self.content_location[content]
        path = self.shortest_path[receiver][source]
        # handle (and log if required) actual request 
        for hop in range(1, len(path)):
            u = path[hop - 1]
            v = path[hop]
            if log: self.link_logger.log_link_info(time, u, v, PACKET_TYPE_INTEREST, content, self.link_type[(u,v)])
            if v == source:
                if log: self.cache_logger.log_cache_info(time, EVENT_SERVER_HIT, content, receiver, 'N/A', source)
                serving_node = v
                break
            if get_stack(self.topology, v)[0] == 'cache':
                if self.caches[v].has_content(content):
                    if log: self.cache_logger.log_cache_info(time, EVENT_CACHE_HIT, content, receiver, v, source)
                    serving_node = v
                    break
        path = self.shortest_path[serving_node][receiver]
        
        # get the cache with maximum betweenness centrality
        # if there are more than one cache with max betw then pick the one
        # closer to the receiver
        max_betw = -1
        selected_cache = None
        for v in path:
            if get_stack(self.topology, v)[0] == 'cache':
                if self.betw[v] >= max_betw:
                    selected_cache = v

        for hop in range(1, len(path)):
            u = path[hop - 1]
            v = path[hop]
            if v == selected_cache:
                self.caches[v].store(content)
            if log: self.link_logger.log_link_info(time, u, v, PACKET_TYPE_DATA, content, self.link_type[(u,v)])
            

# List of all implemented strategies
# This dictionary must stay at the bottom of this file otherwise it would not
# work
# NOTE: Could implement all this using decorator, but I preferred leaving this
# here so that I can comment out unneeded strategies easily  
strategy_impl = {
         'CEE+LRU':     CeeLru,
         'HrSymm':      HashrouteSymmetric,
         'HrAsymm':     HashrouteAsymmetric,
         'HrHybStr02':  HashrouteHybridStretch,
         'HrHybSymMC':  HashrouteHybridSymmMCast,
         'CL4M':        Cl4m,
         'ProbCache':   ProbCache,
         'HrMCast':     HashrouteMulticast,
         'NoCache':     NoCache
                } 