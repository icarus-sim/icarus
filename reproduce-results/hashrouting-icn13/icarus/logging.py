"""
Logger classes for writing to files
"""

# List of all events
import random, shutil
from os import path
from collections import defaultdict
from multiprocessing import Semaphore
from icarus.util import ZipfDistribution
import icarus.config as config


EVENT_CACHE_HIT = 'CH'
EVENT_CACHE_MISS = 'CM'
EVENT_SERVER_HIT = 'SH'
EVENT_ISSUE_INTEREST = 'I' # receiver sends interest packet
EVENT_RECEIVE_DATA = 'D'   # receiver receives data packet

PACKET_TYPE_INTEREST = 'I'
PACKET_TYPE_DATA = 'D'

# If True, it will create CACHE, LINK and STRETCH log files with one line per event
# If False, it will only write the summary files (this option saves space on disk dramatically)
write_log = config.LOG_EVERYTHING
parallel_exec = config.PARALLEL_EXEC

class BaseLogger(object):
    
    def __init__(self, file_name, buf_size=5000, write_log=write_log):
        self.write_log = write_log
        if not self.write_log:
            return
        self.tmp = "/tmp/hashroute_%032x" % random.getrandbits(128)
        self.target = file_name
        self.f = open(self.tmp, 'w')
        self.lines = []
        self.buf_size = buf_size
        self.buf_count = 0 

    def append(self, line):
        """
        Write line on a buffer that will be flushed periodically.
        Note: do not add new-line char, this is added automatically
        """
        if not self.write_log:
            return
        self.lines.append(line)
        self.buf_count += 1
        if self.buf_count % self.buf_size == 0:
            # flush the buffer and write all on file
            self.f.write('\n'.join(self.lines))
            self.f.write('\n')
            self.lines = []
    
    def append_push(self, line):
        """
        Write line that will be written on file immediately.
        Note: do not add new-line char, this is added automatically
        """
        if not self.write_log:
            return
        self.f.write(line)
        self.f.write('\n')
        self.f.flush()

    def close(self):
        """
        write up buffer and close file
        """
        if not self.write_log:
            return
        self.f.write('\n'.join(self.lines))
        self.f.flush()
        self.f.close()
        shutil.move(self.tmp, self.target)


class LinkLogger(BaseLogger):
    """
    Logger for link utilization information
    """
    def __init__(self, file_name, data_interest_size_ratio=10):
        """
        Constructor
        """
        super(LinkLogger, self).__init__(file_name=file_name)
        self.append_push('Time\tFrom\tTo\tPckType\tContentId\tLinkType')
        self.interest_count = defaultdict(int)
        self.data_count = defaultdict(int)
        self.disr = data_interest_size_ratio
        self.t_start = -1
        self.t_end = 1

    def log_link_info(self, time, from_node, to_node, packet_type, content_id, link_type):
        """
        Log link traversing event
        """
        # set start and end time (for scaling of network load)
        if self.t_start < 0: self.t_start = time
        self.t_end = time
        self.append('%s\t%s\t%s\t%s\t%s\t%s' 
                    % (str(time), str(from_node), str(to_node),
                       str(packet_type), str(content_id), str(link_type)))
        if packet_type == PACKET_TYPE_INTEREST: self.interest_count[link_type] += 1
        elif packet_type == PACKET_TYPE_DATA: self.data_count[link_type] += 1
        
    def network_load(self):
        """
        Return network load, a dict of average network loads keyed by link
        type, e.g. 'internal' or 'external'
        """
        return dict([(l, (self.interest_count[l] + self.disr*self.data_count[l])/float(self.t_end - self.t_start)) for l in self.interest_count])



class CacheLogger(BaseLogger):
    """
    Logger for requests, cache and server hits
    """
    
    def __init__(self, file_name):
        """
        Constructor
        """
        super(CacheLogger, self).__init__(file_name=file_name)
        self.append_push('Time\tEvent\tContent\tRecvr\tCache\tServer')
        self.cache_hit_count = 0
        self.server_hit_count = 0
    
    def log_cache_info(self, time, event, content, receiver, cache, server):
        """
        Log cache-related event, i.e. cache hit, cache miss, server hit and
        so on
        """
        self.append('%s\t%s\t%s\t%s\t%s\t%s' 
                    % (str(time), str(event), str(content),
                       str(receiver), str(cache), str(server)))
        # Analysis on logged data
        if event == EVENT_SERVER_HIT: self.server_hit_count += 1
        elif event == EVENT_CACHE_HIT: self.cache_hit_count += 1
    
    def cache_hit_ratio(self):
        """
        Return total cache hit ratio
        """
        return 0 if self.cache_hit_count == 0 else float(self.cache_hit_count) / (self.cache_hit_count + self.server_hit_count)
        

class DelayLogger(BaseLogger):
    """
    Logger for RTT of request/response pairs
    """
    
    def __init__(self, file_name):
        """
        Constructor
        """
        super(DelayLogger, self).__init__(file_name=file_name)
        self.append_push('Time\tReceiver\tSource\tContent\tReqDelay\tRespDelay\tTotalDelay')
        self.event_count = 0
        self.rtt = 0

    def log_delay_info(self, time, receiver, source, content, req_delay, resp_delay):
        """
        Log delay of requests and responses
        """
        # Analysis on logged data
        curr_rtt = req_delay + resp_delay
        self.event_count += 1
        self.rtt += curr_rtt
        self.append('%s\t%s\t%s\t%s\t%s\t%s\t%s' 
                    % (str(time), str(receiver), str(source),
                       str(content), str(req_delay), str(resp_delay), str(curr_rtt)))

    def rtt(self):
        """
        Return average RTT over simulation scenario
        """
        return 0 if self.event_count == 0 else float(self.rtt) / (self.event_count)



class StretchLogger(BaseLogger):
    """
    Logger for stretch of paths
    """
    
    def __init__(self, file_name):
        """
        Constructor
        """
        super(StretchLogger, self).__init__(file_name=file_name)
        self.append_push('Time\tReceiver\tSource\tContent\tOptimalPathLength\tActualDataPathLength\tStretch')
        self.event_count = 0
        self.path_stretch = 0

    def log_stretch_info(self, time, receiver, source, content, optimal_path_len, actual_path_len):
        """
        Log stretch of path
        """
        # Analysis on logged data
        stretch = float(actual_path_len) - float(optimal_path_len)
        self.event_count += 1
        self.path_stretch += stretch
        self.append('%s\t%s\t%s\t%s\t%s\t%s\t%s' 
                    % (str(time), str(receiver), str(source),
                       str(content), str(optimal_path_len), str(actual_path_len), str(stretch)))

    def path_stretch(self):
        """
        Return absolute path stretch
        """
        return 0 if self.event_count == 0 else float(self.path_stretch) / (self.event_count)
        


class BaseSummary(object):
    """
    Base class for summary files
    """
    # Static variable. It is a dictionary of semaphores keyed by file name.
    # This is to ensure that there is one semaphore per summary file.
    semaphore_dict = defaultdict(Semaphore)
    
    def __init__(self, summary_dir, file_name, header):
        """
        Constructor
        
        Parameters
        ----------
        header : list
            List of names of parameters to be logged
        """
        self.sep = '\t'
        f_name = path.join(summary_dir, file_name)
        if parallel_exec: 
            self.semaphore = self.semaphore_dict[f_name]
            self.semaphore.acquire()
        is_new_file = not path.isfile(f_name)
        self.f = open(f_name, 'a')
        if is_new_file:
            self.f.write(self.sep.join(header) + '\n')
            self.f.flush()
        if parallel_exec: self.semaphore.release()
    
    def write_summary(self, entry):
        """
        Write line to summary file
        
        Parameters
        ----------
        entry : list
            List of values of an entry
        """
        if parallel_exec: self.semaphore.acquire()
        self.f.write(self.sep.join(entry) + '\n')
        self.f.flush()
        if parallel_exec: self.semaphore.release()
        
    def close(self):
        if parallel_exec: self.semaphore.acquire()
        if not self.f.closed:
            self.f.close()
        if parallel_exec: self.semaphore.release()


class NetworkLoadSummary(BaseSummary):
    """
    Object modelling summary file of network loads
    """
    
    def __init__(self, summary_dir):
        """
        Parameters
        ----------
        summary_dir : str
            Directory where the summary is to be placed
        """
        super(NetworkLoadSummary, self).__init__(summary_dir, 'SUMMARY_NETWORK_LOAD.txt', ['Scenario', 'LinkType', 'NetworkLoad'])
    
    def write_summary(self, scenario, network_load):
        for link_type in network_load:
            super(NetworkLoadSummary, self).write_summary([str(scenario), str(link_type), str(network_load[link_type])])
        super(NetworkLoadSummary, self).close()

class CacheHitRatioSummary(BaseSummary):
    """
    Object modelling summary file of cache hit ratios
    """
    
    def __init__(self, summary_dir):
        """
        Parameters
        ----------
        summary_dir : str
            Directory where the summary is to be placed
        """
        super(CacheHitRatioSummary, self).__init__(summary_dir, 'SUMMARY_CACHE_HIT_RATIO.txt', ['Scenario', 'CacheHitRatio'])
 
    def write_summary(self, scenario, cache_hit_ratio):
        """
        Write summary and close file
        """
        super(CacheHitRatioSummary, self).write_summary([str(scenario), str(cache_hit_ratio)])
        super(CacheHitRatioSummary, self).close()
 
    def append_optimal_cache_hit(self, topology, alpha, net_cache, n_contents):
        """
        Append to the file a list of entries with the analytically calculated
        optimal cache hit ratio
        """
        for a in alpha:
            cdf = list(ZipfDistribution(alpha=a, N=n_contents).get_cdf())
            for c in net_cache:
                p = cdf[int(n_contents*c)-1]
                for t in topology:
                    super(CacheHitRatioSummary, self).write_summary(['T=%s@C=%s@A=%s@S=Optimal' % (t, str(c), str(a)), '%s' % str(p)])
        super(CacheHitRatioSummary, self).close()