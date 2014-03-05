"""Network Model-View-Controller (MVC)
"""
import networkx as nx
import fnss

from icarus.registry import cache_policy_register


__all__ = [
    'NetworkModel',
    'NetworkView',
    'NetworkController'
          ]


class NetworkView(object):
    
    def __init__(self, model):
        """Constructor
        
        Parameters
        ----------
        model : NetworkModel
            The network model instance
        """
        if not isinstance(model, NetworkModel):
            raise ValueError('The model argument must be an instance of '
                             'NetworkModel')
        self.model = model
    
    def content_locations(self, k):
        """Return a set of all current locations of a specific content.
        
        This include both persistent content sources and temporary caches. 
        
        Parameters
        ----------
        k : any hashable type
            The content identifier
        
        Returns
        -------
        nodes : set
            A set of all nodes currently storing the given content
        """
        loc = set(v for v in self.model.caches if self.model.caches[v].has(k))
        loc.add(self.content_source(k))
        return loc
    
    def content_source(self, k):
        """
        Return the node identifier where the content is persistently stores.
        
        Parameters
        ----------
        k : any hashable type
            The content identifier
        
        Returns
        -------
        node : any hashable type
            The node persistently storing the given content
        """
        return self.model.content_source[k]
        
    def shortest_path(self, s, t):
        """Return the shortest path from *s* to *t*
        
        Parameters
        ----------
        s : any hashable type
            Origin node
        t : any hashable type
            Destination node
        
        Returns
        -------
        shortest_path : list
            List of nodes of the shortest path (origin and destination
            included)
        """
        return self.model.shortest_path[s][t]

    def link_type(self, u, v):
        """Return the type of link *(u, v)*.
        
        Type can be either *internal* or *external*
        
        Parameters
        ----------
        u : any hashable type
            Origin node
        v : any hashable type
            Destination node
        
        Returns
        -------
        link_type : str
            The link type
        """
        return self.model.link_type[(u, v)]
    
    def link_delay(self, u, v):
        """Return the delay of link *(u, v)*.
        
        Parameters
        ----------
        u : any hashable type
            Origin node
        v : any hashable type
            Destination node
        
        Returns
        -------
        delay : float
            The link delay
        """
        return self.model.link_delay[(u, v)]
    
    def topology(self):
        """Return the network topology
        
        Returns
        -------
        topology : fnss.Topology
            The topology object
        
        Notes
        -----
        The topology object returned by this method must not be modified by the
        caller. This object can only be modified through the NetworkController.
        Changes to this object will lead to inconsistent network state.
        """
        return self.model.topology
    
    def caches(self):
        """Returns a dictionary mapping caching nodes and cache space
        
        Returns
        -------
        caches : dict
            dict mapping caching nodes and cache space
        """
        return self.model.cache_size


class NetworkModel(object):
    """Models the internal state of the network
    """
    
    def __init__(self, topology, shortest_path=None):
        """Constructors
        
        Parameters
        ----------
        topology : fnss.Topology
            The topology object
        shortest_path : dict of dict, optional
            The all-pair shortest paths of the network
        """
        # Filter inputs
        if not isinstance(topology, fnss.Topology):
            raise ValueError('The topology argument must be an instance of '
                             'fnss.Topology or any of its subclasses.')
        
        # Shortest paths of the network
        self.shortest_path = shortest_path if shortest_path is not None \
                             else nx.all_pairs_shortest_path(topology)
        
        # Network topology
        self.topology = topology
        
        # Dictionary mapping each content object to its source
        # dict of location of contents keyed by content ID
        self.content_source = {}
        
        # Dictionary of cache sizes keyed by node
        self.cache_size = {}
        
        # Dictionary of link types (internal/external)
        self.link_type = nx.get_edge_attributes(topology.to_directed(), 'type')
        
        self.link_delay = fnss.get_delays(topology.to_directed())
        
        policy_name = topology.graph['cache_policy']
        # Initialize attributes
        for node in topology.nodes_iter():
            stack_name, stack_props = fnss.get_stack(topology, node)
            if stack_name == 'cache':
                self.cache_size[node] = stack_props['size']
            elif stack_name == 'source':
                contents = stack_props['contents']
                for content in contents:
                    self.content_source[content] = node
        cache_size = dict((node, fnss.get_stack(topology, node)[1]['size'])
                          for node in topology.nodes_iter()
                          if fnss.get_stack(topology, node)[0] == 'cache')
        # The actual cache object storing the content
        self.caches = dict((node, cache_policy_register[policy_name](cache_size[node]))
                            for node in cache_size)


class NetworkController(object):
    """Network controller
    """
    
    def __init__(self, model):
        """Constructor
        
        Parameters
        ----------
        model : NetworkModel
            Instance of the network model
        """
        self.session = None
        self.model = model
        self.collector = None
    
    
    def attach_collector(self, collector):
        """Attaches a data collector to which all events will be reported.
        
        Parameters
        ----------
        collector : DataCollector
            The data collector
        """
        self.collector = collector
        
    def detach_collector(self):
        """Detaches the data collector.
        """
        self.collector = None
    
    def start_session(self, timestamp, receiver, content, log):
        """Instruct the controller to start a new session (i.e. the retrieval
        of a content).
        
        Parameters
        ----------
        timestamp : int
            The timestamp of the event
        receiver : any hashable type
            The receiver node requesting a content
        content : any hashable type
            The content identifier requested by the receiver
        log : bool
            *True* if this session needs to be reported to the collector,
            *False* otherwise
        """
        self.session = dict(timestamp=timestamp,
                            receiver=receiver,
                            content=content,
                            log=log)
        if self.collector is not None and self.session['log']:
            self.collector.start_session(timestamp, receiver, content)
    
    def forward_request_path(self, s, t, path=None):
        """Forward a request from node *s* to node *t* over the provided path.
                
        Parameters
        ----------
        s : any hashable type
            Origin node
        t : any hashable type
            Destination node
        path : list, optional
            The path to use. If not provided, shortest path is used
        """
        if path is None:
            path = self.model.shortest_path[s][t]
        for hop in range(1, len(path)):
            u = path[hop - 1]
            v = path[hop]
            self.forward_request_hop(u, v)
    
    def forward_content_path(self, u, v, path=None):
        """Forward a content from node *s* to node *t* over the provided path.
                
        Parameters
        ----------
        s : any hashable type
            Origin node
        t : any hashable type
            Destination node
        path : list, optional
            The path to use. If not provided, shortest path is used
        """
        if path is None:
            path = self.model.shortest_path[u][v]
        for hop in range(1, len(path)):
            u = path[hop - 1]
            v = path[hop]
            self.forward_content_hop(u, v)
    
    def forward_request_hop(self, u, v):
        """Forward a request over link  u -> v.
                
        Parameters
        ----------
        u : any hashable type
            Origin node
        v : any hashable type
            Destination node
        """
        if self.collector is not None and self.session['log']:
            self.collector.request_hop(u, v)
    
    def forward_content_hop(self, u, v):
        """Forward a content over link  u -> v.
                
        Parameters
        ----------
        u : any hashable type
            Origin node
        v : any hashable type
            Destination node
        """
        if self.collector is not None and self.session['log']:
            self.collector.content_hop(u, v)
    
    def put_content(self, node):
        """Store content in the specified node.
        
        The node must have a cache stack and the actual insertion of the
        content is executed according to the caching policy. If the caching
        policy has a selective insertion policy, then content may not be
        inserted.
        
        Parameters
        ----------
        node : any hashable type
            The node where the content is inserted
        """
        if node in self.model.caches:
            self.model.caches[node].put(self.session['content'])
    
    def get_content(self, node):
        """Get a content from a server or a cache.

        Parameters
        ----------
        node : any hashable type
            The node where the content is retrieved
        
        Returns
        -------
        content : bool
            True if the content is available, False otherwise
        """
        if node in self.model.caches:
            cache_hit = self.model.caches[node].get(self.session['content'])
            if cache_hit:
                if self.session['log']:
                    self.collector.cache_hit(node)
            return cache_hit
        name, props = fnss.get_stack(self.model.topology, node)
        if name == 'source' and self.session['content'] in props['contents']:
            if self.collector is not None and self.session['log']:
                self.collector.server_hit(node)
            return True
        else:
            return False
    
    def end_session(self, success=True):
        """Close a session
        
        Parameters
        ----------
        success : bool, optional
            *True* if the session was completed successfully, *False* otherwise
        """
        if self.collector is not None and self.session['log']:
            self.collector.end_session(success)
        self.session = None

    def remove_link(self, u, v):
        raise NotImplementedError('Method not yet implemented')

    def restore_link(self, u, v):
        raise NotImplementedError('Method not yet implemented')
    
    def remove_node(self, v):
        raise NotImplementedError('Method not yet implemented')
    
    def restore_node(self, v):
        raise NotImplementedError('Method not yet implemented')
    

