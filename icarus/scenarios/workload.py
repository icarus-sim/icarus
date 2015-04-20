"""Traffic workloads

Every traffic workload to be used with Icarus must be modelled as an iterable
class, i.e. a class with at least an __init__ method (through which it is
inizialized, with values taken from the configuration file) and an __iter__
method that is called to return a new event.

Each workload must expose the 'contents' attribute which is an iterable of
all content identifiers. This is need for content placement
"""
import random
import csv

from icarus.tools import TruncatedZipfDist
from icarus.registry import register_workload

__all__ = [
        'StationaryWorkload',
        'GlobetraffWorkload',
        'TraceDrivenWorkload'
           ]


@register_workload('STATIONARY')
class StationaryWorkload(object):
    """This function generates events on the fly, i.e. instead of creating an 
    event schedule to be kept in memory, returns an iterator that generates
    events when needed.
    
    This is useful for running large schedules of events where RAM is limited
    as its memory impact is considerably lower.
    
    These requests are Poisson-distributed while content popularity is
    Zipf-distributed
    
    Parameters
    ----------
    topology : fnss.Topology
        The topology to which the workload refers
    n_contents : int
        The number of content object
    alpha : float
        The Zipf alpha parameter
    rate : float
        The mean rate of requests per second
    n_warmup : int
        The number of warmup requests (i.e. requests executed to fill cache but
        not logged)
    n_measured : int
        The number of logged requests after the warmup
    
    Returns
    -------
    events : iterator
        Iterator of events. Each event is a 2-tuple where the first element is
        the timestamp at which the event occurs and the second element is a
        dictionary of event attributes.
    """
    def __init__(self, topology, n_contents, alpha, rate=12.0,
                    n_warmup=10**5, n_measured=4*10**5, seed=None, **kwargs):
        self.receivers = [v for v in topology.nodes_iter()
                     if topology.node[v]['stack'][0] == 'receiver']
        self.zipf = TruncatedZipfDist(alpha, n_contents)
        self.n_contents = n_contents
        self.contents = range(1, n_contents + 1)
        self.alpha = alpha
        self.rate = rate
        self.n_warmup = n_warmup
        self.n_measured = n_measured
        random.seed(seed)
        
    def __iter__(self):
        req_counter = 0
        t_event = 0.0
        while req_counter < self.n_warmup + self.n_measured:
            t_event += (random.expovariate(self.rate))
            receiver = random.choice(self.receivers)
            content = int(self.zipf.rv())
            log = (req_counter >= self.n_warmup)
            event = {'receiver': receiver, 'content': content, 'log': log}
            yield (t_event, event)
            req_counter += 1
        raise StopIteration()


@register_workload('GLOBETRAFF')
class GlobetraffWorkload(object):
    """Parse requests from GlobeTraff workload generator
    
    Parameters
    ----------
    topology : fnss.Topology
        The topology to which the workload refers
    content_file : str
        The GlobeTraff content file
    request_file : str
        The GlobeTraff request file
    """
    
    def __init__(self, topology, content_file, request_file, **kwargs):
        """Constructor
        """
        self.receivers = [v for v in topology.nodes_iter() 
                     if topology.node[v]['stack'][0] == 'receiver']
        self.n_contents = 0
        with open(content_file, 'r') as f:
            reader = csv.reader(f, delimiter='\t')
            for content, popularity, size, app_type in reader:
                self.n_contents = max(self.n_contents, content)
        self.n_contents += 1
        self.contents = range(self.n_contents)
        self.request_file = request_file
        
    def __iter__(self):
        with open(self.request_file, 'r') as f:
            reader = csv.reader(f, delimiter='\t')
            for timestamp, content, size in reader:
                yield (timestamp, content)
        raise StopIteration()

@register_workload('TRACE_DRIVEN')
class TraceDrivenWorkload(object):
    """Parse requests from a generic request list file.
    
    This file lists for each line the ID of a requested content. The output
    workload maps randomly requests of the trace file to receiver nodes of the
    topology
    """
    def __init__(self, topology, reqs_file, contents_file, n_contents, n_warmup, n_measured, rate=12.0, **kwargs):
        self.buffering = 64*1024*1024 # Set high buffering to avoid frequent one-line reads
        self.n_contents = n_contents
        self.n_warmup = n_warmup
        self.n_measured = n_measured
        self.reqs_file = reqs_file
        self.rate = rate
        self.receivers = [v for v in topology.nodes_iter() 
                          if topology.node[v]['stack'][0] == 'receiver']
        self.contents = []
        with open(contents_file, 'r', buffering=self.buffering) as f:
            for content in f:
                self.contents.append(content)
        
    def __iter__(self):
        req_counter = 0
        t_event = 0.0
        with open(self.reqs_file, 'r', buffering=self.buffering) as f:
            for content in f:
                t_event += (random.expovariate(self.rate))
                receiver = random.choice(self.receivers)
                log = (req_counter >= self.n_warmup)
                event = {'receiver': receiver, 'content': content, 'log': log}
                yield (t_event, event)
                req_counter += 1
                if(req_counter >= self.n_warmup + self.n_measured):
                    raise StopIteration()
            raise ValueError("Trace did not contain enough requests")
