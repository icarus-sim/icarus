"""
Classes which can be used to manipulate results of simulations
"""
from numpy import array, genfromtxt, ceil, zeros, sort, cumsum
from collections import Counter, defaultdict
from icarus.logging import EVENT_CACHE_HIT, EVENT_SERVER_HIT, \
                              PACKET_TYPE_INTEREST, PACKET_TYPE_DATA


class SummaryAnalyzer(object):
    """
    parser for summary files for analysis purposes
    """
    
    def __init__(self, summary_file, scenario_params=['T', 'C', 'A', 'S']):
        """
        Constructor
        """
        self.data = genfromtxt(summary_file, dtype=None, delimiter='\t', names=True)
        if scenario_params == None or len(scenario_params) == 0:
            return
        self.param = {}
        s = [SummaryAnalyzer.parse_scenario_id(s) for s in self.data['Scenario']]
        for k in scenario_params:
            self.param[k] = array([p[k] for p in s])
            
    @classmethod
    def parse_scenario_id(cls, scenario_id):
        """
        Parse a scenario id string encoded as K1=V1@K2=V2@ ... @KN=VN
        
        Returns
        -------
        params : dict
            A dictionary of values V keyed by K
        """
        return dict([(p.split('=')) for p in scenario_id.split('@')])


class LinkDataAnalyzer(object):
    """Object to manipulate data from link logs"""
    
    def __init__(self, link_log_file):
        """
        Save data into instance array which can be later accessed for processing
        """
        self.data = genfromtxt(link_log_file, dtype=None, delimiter='\t', names=True)
        #Time    From    To    PckType    ContentId
        self.time = self.data['Time']
        self.from_node = self.data['From']
        self.to_node = self.data['To']
        self.packet_type = self.data['PckType']
        self.content = self.data['ContentId']
        self.link_type= self.data['LinkType']
    
    def per_link_load(self, link_type='internal', data_interest_size_ratio=10):
        """
        Return a dictionary of link loads keyed by link ID. Link ID is a tuple
        (u, v)
        """
        links = list(set(zip(self.from_node, self.to_node)))
        t_start = self.time[0]
        t_end = self.time[len(self.time) - 1]
        link_load = defaultdict(float)
        for u, v in links:
            cond = (self.link_type == link_type) & (self.from_node == u) & (self.to_node == v)
            load_interest = len(self.packet_type[cond & (self.packet_type == PACKET_TYPE_INTEREST)])
            load_data = len(self.packet_type[cond & (self.packet_type == PACKET_TYPE_DATA)]) 
            link_load[(u, v)] = float(load_interest + data_interest_size_ratio*load_data)/(t_end - t_start)
        return link_load
            
    def network_load_average(self, time_unit, interest_size, data_size, link_type=None):
        """
        Return average network load
        
        This can be found already in the summary files produced by the link logger
        """
        t_start = self.time[0]
        t_end = self.time[len(self.time) - 1]
        link_type_cond = True if link_type is None else self.link_type == link_type
        n_interest = len(self.packet_type[(self.packet_type == PACKET_TYPE_INTEREST) & link_type_cond])
        n_data = len(self.packet_type[(self.packet_type == PACKET_TYPE_DATA) & link_type_cond])
        return float((interest_size*n_interest) + (data_size*n_data)) * (float(time_unit)/(t_end - t_start))
    
    def network_load_evolution(self, time_unit, interest_size, data_size, granularity, link_type=None):
        """
        Return array representing evolution of network load over time
        """
        t_start = self.time[0]
        t_end = self.time[len(self.time) - 1]
        n_samples = ceil((t_end - t_start)/granularity)
        network_load = zeros(n_samples)
        link_type_cond = True if link_type is None else self.link_type == link_type
        for i in range(int(n_samples)):
            t_min = t_start + i*granularity
            t_max = t_min + granularity
            n_interest = len(self.packet_type[(self.packet_type == PACKET_TYPE_INTEREST) &
                                              (self.time >= t_min) &
                                              (self.time < t_max) &
                                              link_type_cond]) 
            n_data = len(self.packet_type[(self.packet_type == PACKET_TYPE_DATA) &
                                          (self.time >= t_min) &
                                          (self.time < t_max) &
                                          link_type_cond])
            network_load[i] = float((interest_size*n_interest) + (data_size*n_data)) * (float(time_unit)/granularity)
        return network_load

    
class CacheDataAnalyzer(object):
    """
    Object to manipulate data from cache logs
    """
    
    def __init__(self, cache_log_file):
        """
        Save data into instance array which can be later accessed for processing
        """
        self.data = genfromtxt(cache_log_file, dtype=None, delimiter='\t', names=True)
        #Time    Event    Content    Recvr    Cache    Server
        self.time = self.data['Time']
        self.event = self.data['Event']
        self.content = self.data['Content']
        self.receiver = self.data['Recvr']
        self.cache = self.data['Cache']
        self.server = self.data['Server']
        
    def cache_hit_ratio_total(self):
        """
        Return global cache hit ratio
        
        This can be found already in the summary files produced by the cache logger
        """
        # Case of no events at all (e.g. no caches)
        if len(self.time) == 0:
            return 0.0
        n_cache_hit = len(self.event[self.event == EVENT_CACHE_HIT])
        n_server_hit = len(self.event[self.event == EVENT_SERVER_HIT])
        return float(n_cache_hit)/(n_cache_hit + n_server_hit)

    def cache_hit_ratio_evolution(self, granularity):
        """
        Return an array of cache hit ratio calculated every "granularity" time
        units.
        """
        # Case of no events at all (e.g. no caches)
        if len(self.time) == 0:
            return array([0.0])
        t_start = self.time[0]
        t_end = self.time[len(self.time) - 1]
        n_samples = ceil((t_end - t_start)/granularity)
        cache_hit_ratio = zeros(n_samples)
        for i in range(int(n_samples)):
            t_min = t_start + i*granularity
            t_max = t_min + granularity
            n_cache_hit = len(self.event[(self.event == EVENT_CACHE_HIT) &
                                         (self.time >= t_min) &
                                         (self.time < t_max)])
            n_server_hit = len(self.event[(self.event == EVENT_SERVER_HIT) &
                                          (self.time >= t_min) &
                                          (self.time < t_max)])
            cache_hit_ratio[i] = float(n_cache_hit)/(n_cache_hit + n_server_hit) \
                                 if (n_cache_hit + n_server_hit) > 0 else 0
        return cache_hit_ratio
    

class DelayAnalyzer(object):
    """
    Object to manipulate data from delay logs
    """
    
    def __init__(self, delay_log_file):
        """
        Save data into instance array which can be later accessed for processing
        """
        self.data = genfromtxt(delay_log_file, dtype=None, delimiter='\t', names=True)
        self.time = self.data['Time']
        self.receiver = self.data['Receiver']
        self.source = self.data['Source']
        self.content = self.data['Content']
        self.req_delay = self.data['ReqDelay']
        self.resp_delay = self.data['RespDelay']
        self.total_delay = self.data['TotalDelay']

    def cdf(self):
        """Return empirical CDF of RTT
        """
        freq_dict = Counter(self.stretch) 
        sorted_unique_data = sort(freq_dict.keys())
        freqs = zeros(len(sorted_unique_data))
        for i in range(len(sorted_unique_data)):
            freqs[i] = freq_dict[sorted_unique_data[i]]
        cdf = cumsum(freqs)
        cdf = cdf / float(cdf[len(cdf) - 1]) # normalize
        return sorted_unique_data, cdf



class PathStretchAnalyzer(object):
    """
    Object to manipulate data from path stretch logs
    """
    
    def __init__(self, stretch_log_file):
        """
        Save data into instance array which can be later accessed for processing
        """
        self.data = genfromtxt(stretch_log_file, dtype=None, delimiter='\t', names=True)
        self.time = self.data['Time']
        self.receiver = self.data['Receiver']
        self.source = self.data['Source']
        self.content = self.data['Content']
        self.optimal_path_length = self.data['OptimalPathLength']
        self.actual_path_length = self.data['ActualDataPathLength']
        self.stretch = self.data['Stretch']

    def cdf(self):
        """Return empirical CDF of path stretch
        """
        freq_dict = Counter(self.stretch) 
        sorted_unique_data = sort(freq_dict.keys())
        freqs = zeros(len(sorted_unique_data))
        for i in range(len(sorted_unique_data)):
            freqs[i] = freq_dict[sorted_unique_data[i]]
        cdf = cumsum(freqs)
        cdf = cdf / float(cdf[len(cdf) - 1]) # normalize
        return sorted_unique_data, cdf

