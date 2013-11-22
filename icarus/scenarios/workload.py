"""Functions for generating traffic workloads 
"""
import random
from icarus.tools import TruncatedZipfDist


__all__ = [
        'uniform_req_gen',
        'globetraff_req_gen'
           ]


def uniform_req_gen(topology, n_contents, alpha, rate=12.0,
                    n_warmup=10**5, n_measured=4*10**5, seed=None):
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
    receivers = [v for v in topology.nodes_iter()
                 if topology.node[v]['stack'][0] == 'receiver']
    zipf = TruncatedZipfDist(alpha, n_contents)
    random.seed(seed)
    
    req_counter = 0
    t_event = 0.0
    while req_counter < n_warmup + n_measured:
        t_event += (random.expovariate(rate))
        receiver = random.choice(receivers)
        content = int(zipf.rv())
        log = (req_counter >= n_warmup)
        event = {'receiver': receiver, 'content': content, 'log': log}
        yield (t_event, event)
        req_counter += 1
    raise StopIteration()

def globetraff_req_gen(topology, content_file, request_file):
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
    raise NotImplementedError('Not yet implemented')