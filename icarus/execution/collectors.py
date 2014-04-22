"""This module contains performance metrics loggers
"""
from __future__ import division
import sys
import collections

from icarus.registry import register_data_collector
from icarus.tools import cdf
from icarus.util import inheritdoc


__all__ = [
    'DataCollector',
    'CollectorProxy',
    'CacheHitRatioCollector',
    'LinkLoadCollector',
    'LatencyCollector',
    'PathStretchCollector',
    'TestCollector'
           ]


class DataCollector(object):
    """Object collecting notifications about simulation events and measuring
    relevant metrics.
    """
    
    def __init__(self, view, **params):
        """Constructor
        
        Parameters
        ----------
        view : NetworkView
            An instance of the network view
        params : keyworded parameters
            Collector parameters
        """
        self.view = view
    
    def start_session(self, timestamp, receiver, content):
        """Notifies the collector that a new network session started.
        
        A session refers to the retrieval of a content from a receiver, from
        the issuing of a content request to the delivery of the content.
        
        Parameters
        ----------
        timestamp : int
            The timestamp of the event
        receiver : any hashable type
            The receiver node requesting a content
        content : any hashable type
            The content identifier requested by the receiver
        """
        pass
    
    def cache_hit(self, node):
        """Reports that the requested content has been served by the cache at
        node *node*.
        
        Parameters
        ----------
        node : any hashable type
            The node whose cache served the content
        """
        pass

    def server_hit(self, node):
        """Reports that the requested content has been served by the server at
        node *node*.
        
        Parameters
        ----------
        node : any hashable type
            The server node which served the content
        """
        pass
    
    def request_hop(self, u, v):
        """Reports that a request has traversed the link *(u, v)*
        
        Parameters
        ----------
        u : any hashable type
            Origin node
        v : any hashable type
            Destination node
        """
        pass
    
    def content_hop(self, u, v):
        """Reports that a content has traversed the link *(u, v)*
        
        Parameters
        ----------
        u : any hashable type
            Origin node
        v : any hashable type
            Destination node
        """
        pass
    
    def end_session(self, success=True):
        """Reports that the session is closed, i.e. the content has been
        successfully delivered to the receiver or a failure blocked the 
        execution of the request
        
        Parameters
        ----------
        success : bool, optional
            *True* if the session was completed successfully, *False* otherwise
        """
        pass
    
    def results(self):
        """Returns the aggregated results measured by the collector.
        
        Returns
        -------
        results : dict
            Dictionary mapping metric with results.
        """
        pass

# Note: The implementation of CollectorProxy could be improved to avoid having
# to rewrite almost identical methods, for example by playing with __dict__
# attribute. However, it was implemented this way to make it more readable and 
# easier to understand.
class CollectorProxy(DataCollector):
    """This class acts as a proxy for all concrete collectors towards the
    network controller.
    
    An instance of this class registers itself with the network controller and
    it receives notifications for all events. This class is responsible for
    dispatching events of interests to concrete collectors.
    """
    
    EVENTS = ('start_session', 'end_session', 'cache_hit', 'server_hit',
              'request_hop', 'content_hop', 'results')
    
    def __init__(self, view, collectors):
        """Constructor
        
        Parameters
        ----------
        view : NetworkView
            An instance of the network view
        collector : list of DataCollector
            List of instances of DataCollector that will be notified of events
        """
        self.view = view
        self.collectors = dict((e,[c for c in collectors if e in type(c).__dict__])
                               for e in self.EVENTS)
    
    @inheritdoc(DataCollector)
    def start_session(self, timestamp, receiver, content):
        for c in self.collectors['start_session']:
            c.start_session(timestamp, receiver, content)
    
    @inheritdoc(DataCollector)
    def cache_hit(self, node):
        for c in self.collectors['cache_hit']:
            c.cache_hit(node)

    @inheritdoc(DataCollector)
    def server_hit(self, node):
        for c in self.collectors['server_hit']:
            c.server_hit(node)
    
    @inheritdoc(DataCollector)
    def request_hop(self, u, v):
        for c in self.collectors['request_hop']:
            c.request_hop(u, v)
    
    @inheritdoc(DataCollector)
    def content_hop(self, u, v):
        for c in self.collectors['content_hop']:
            c.content_hop(u, v)
    
    @inheritdoc(DataCollector)
    def end_session(self, success=True):
        for c in self.collectors['end_session']:
            c.end_session(success)
    
    @inheritdoc(DataCollector)
    def results(self):
        return dict((c.name, c.results()) for c in self.collectors['results'])


@register_data_collector('LINK_LOAD')
class LinkLoadCollector(DataCollector):
    """Data collector measuring the link load
    """
    
    def __init__(self, view, sr=10):
        """Constructor
        
        Parameters
        ----------
        view : NetworkView
            The network view instance
        sr : int
            Size ratio. The average ratio between the size of the content data
            and the request data. For example, if sr = x, then it means that
            the average size of a content is x times the size of a request.
        """
        self.view = view
        self.req_count = collections.defaultdict(int)
        self.cont_count = collections.defaultdict(int)
        if sr <= 0:
            raise ValueError('sr must be positive')
        self.sr = sr
        self.t_start = -1
        self.t_end = 1
    
    @inheritdoc(DataCollector)
    def start_session(self, timestamp, receiver, content):
        if self.t_start < 0:
            self.t_start = timestamp
        self.t_end = timestamp
    
    @inheritdoc(DataCollector)
    def request_hop(self, u, v):
        self.req_count[(u, v)] += 1
    
    @inheritdoc(DataCollector)
    def content_hop(self, u, v):
        self.cont_count[(u, v)] += 1
    
    @inheritdoc(DataCollector)
    def results(self):
        duration = self.t_end - self.t_start
        link_loads = dict((link, (self.req_count[link] + self.sr*self.cont_count[link])/duration) 
                          for link in self.req_count)
        link_loads_int = dict((link, load)
                              for link, load in link_loads.iteritems()
                              if self.view.link_type(*link) == 'internal')
        link_loads_ext = dict((link, load)
                              for link, load in link_loads.iteritems()
                              if self.view.link_type(*link) == 'external')
        mean_load_int = sum(link_loads_int.values())/len(link_loads_int)
        mean_load_ext = sum(link_loads_ext.values())/len(link_loads_ext)
        return {'MEAN_INTERNAL':  mean_load_int, 
                'MEAN_EXTERNAL':  mean_load_ext,
                'PER_LINK_INTERNAL': link_loads_int,
                'PER_LINK_EXTERNAL': link_loads_ext}


@register_data_collector('LATENCY')
class LatencyCollector(DataCollector):
    """Data collector measuring latency, i.e. the delay taken to delivery a
    content.
    """
    
    def __init__(self, view, cdf=False):
        """Constructor
        
        Parameters
        ----------
        view : NetworkView
            The network view instance
        cdf : bool, optional
            If *True*, also collects a cdf of the latency
        """
        self.cdf = cdf
        self.view = view
        self.req_latency = 0.0
        self.sess_count = 0
        self.latency = 0.0
        if cdf:
            self.latency_data = collections.deque()
    
    @inheritdoc(DataCollector)
    def start_session(self, timestamp, receiver, content):
        self.sess_count += 1
        self.sess_latency = 0.0
    
    @inheritdoc(DataCollector)
    def request_hop(self, u, v):
        self.sess_latency += self.view.link_delay(u, v)
    
    @inheritdoc(DataCollector)
    def content_hop(self, u, v):
        self.sess_latency += self.view.link_delay(u, v)
    
    @inheritdoc(DataCollector)
    def end_session(self, success=True):
        if not success:
            return
        if self.cdf:
            self.latency_data.append(self.sess_latency)
        self.latency += self.sess_latency
    
    @inheritdoc(DataCollector)
    def results(self):
        results = {'MEAN': self.latency/self.sess_count}
        if self.cdf:
            results['CDF'] = cdf(self.latency_data) 
        return results


@register_data_collector('CACHE_HIT_RATIO')
class CacheHitRatioCollector(DataCollector):
    """Collector measuring the cache hit ratio, i.e. the portion of content
    requests served by a cache.
    """
    
    def __init__(self, view, content_hits=False):
        """Constructor
        
        Parameters
        ----------
        view : NetworkView
            The NetworkView instance
        content_hits : bool, optional
            If *True* also records cache hits per content instead of just
            globally
        """
        self.cont_hits = content_hits
        self.sess_count = 0
        self.cache_hits = 0
        self.serv_hits = 0
        if self.cont_hits:
            self.curr_cont = None
            self.cont_cache_hits = collections.defaultdict(int)
            self.cont_serv_hits = collections.defaultdict(int)

    @inheritdoc(DataCollector)
    def start_session(self, timestamp, receiver, content):
        self.sess_count += 1
        if self.cont_hits:
            self.curr_cont = content
    
    @inheritdoc(DataCollector)
    def cache_hit(self, node):
        self.cache_hits += 1
        if self.cont_hits:
            self.cont_cache_hits[self.curr_cont] += 1

    @inheritdoc(DataCollector)
    def server_hit(self, node):
        self.serv_hits += 1
        if self.cont_hits:
            self.cont_serv_hits[self.curr_cont] += 1
    
    @inheritdoc(DataCollector)
    def results(self):
        hit_ratio = self.cache_hits/(self.cache_hits + self.serv_hits)
        results = {'MEAN': hit_ratio}
        if self.cont_hits:
            cont_set = set(self.cont_cache_hits.keys() + self.cont_serv_hits.keys())
            cont_hits=dict((self.cont_cache_hits[i]/(self.cont_cache_hits[i] + self.cont_serv_hits[i])) 
                            for i in cont_set)
            results['PER_CONTENT'] = cont_hits
        return results


@register_data_collector('PATH_STRETCH')
class PathStretchCollector(DataCollector):
    """Collector measuring the path stretch, i.e. the ratio between the actual
    path length and the shortest path length.
    """
    
    def __init__(self, view, cdf=False):
        """Constructor
        
        Parameters
        ----------
        view : NetworkView
            The network view instance
        cdf : bool, optional
            If *True*, also collects a cdf of the path stretch
        """
        self.view = view
        self.cdf = cdf
        self.req_path_len = collections.defaultdict(int)
        self.cont_path_len = collections.defaultdict(int)
        self.sess_count = 0
        self.mean_req_stretch = 0.0
        self.mean_cont_stretch = 0.0
        self.mean_stretch = 0.0
        if self.cdf:
            self.req_stretch_data = collections.deque()
            self.cont_stretch_data = collections.deque()
            self.stretch_data = collections.deque()
    
    @inheritdoc(DataCollector)
    def start_session(self, timestamp, receiver, content):
        self.receiver = receiver
        self.source = self.view.content_source(content)
        self.req_path_len = 0
        self.cont_path_len = 0
        self.sess_count += 1

    @inheritdoc(DataCollector)
    def request_hop(self, u, v):
        self.req_path_len += 1
    
    @inheritdoc(DataCollector)
    def content_hop(self, u, v):
        self.cont_path_len += 1
    
    @inheritdoc(DataCollector)
    def end_session(self, success=True):
        if not success:
            return
        req_sp_len = len(self.view.shortest_path(self.receiver, self.source))
        cont_sp_len = len(self.view.shortest_path(self.source, self.receiver))
        req_stretch = self.req_path_len/req_sp_len
        cont_stretch = self.cont_path_len/cont_sp_len
        stretch = (self.req_path_len + self.cont_path_len)/(req_sp_len + cont_sp_len)
        self.mean_req_stretch += req_stretch
        self.mean_cont_stretch += cont_stretch
        self.mean_stretch += stretch
        if self.cdf:
            self.req_stretch_data.append(req_stretch)
            self.cont_stretch_data.append(cont_stretch)
            self.stretch_data.append(stretch)
            
    @inheritdoc(DataCollector)
    def results(self):
        results = {'MEAN': self.mean_stretch/self.sess_count,
                   'MEAN_REQUEST': self.mean_req_stretch/self.sess_count,
                   'MEAN_CONTENT': self.mean_cont_stretch/self.sess_count}
        if self.cdf:
            results['CDF'] = cdf(self.stretch_data)
            results['CDF_REQUEST'] = cdf(self.req_stretch_data)
            results['CDF_CONTENT'] = cdf(self.cont_stretch_data)
        return results
    

@register_data_collector('TEST')
class TestCollector(DataCollector):
    """Collector used for test cases only.
    """
    
    def __init__(self, view):
        """Constructor
        
        Parameters
        ----------
        view : NetworkView
            The network view instance
        output : stream
            Stream on which debug collector writes
        """
        self.view = view
    
    @inheritdoc(DataCollector)
    def start_session(self, timestamp, receiver, content):
        self.session = dict(timestamp=timestamp, receiver=receiver,
                            content=content, request_hops=[], content_hops=[])

    @inheritdoc(DataCollector)
    def cache_hit(self, node):
        self.session['serving_node'] = node

    @inheritdoc(DataCollector)
    def server_hit(self, node):
        self.session['serving_node'] = node

    @inheritdoc(DataCollector)
    def request_hop(self, u, v):
        self.session['request_hops'].append((u, v))
    
    @inheritdoc(DataCollector)
    def content_hop(self, u, v):
        self.session['content_hops'].append((u, v))
    
    @inheritdoc(DataCollector)
    def end_session(self, success=True):
        self.session['success'] = success
    
    def session_summary(self):
        """Return a summary of latest session
        
        Returns
        -------
        session : dict
            Summary of session
        """
        return self.session

    