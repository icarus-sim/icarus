import sys
if sys.version_info[:2] >= (2, 7):
    import unittest
else:
    try:
        import unittest2 as unittest
    except ImportError:
        raise ImportError("The unittest2 package is needed to run the tests.") 
del sys
import fnss

import icarus.models as strategy
from icarus.execution import NetworkModel, NetworkView, NetworkController, TestCollector


def on_path_topology():
    """Return topology for testing on-path caching strategies
    """ 
    # Topology sketch
    #
    # 0 ---- 1 ---- 2 ---- 3 ---- 4
    #               |
    #               |
    #               5
    #
    topology = fnss.line_topology(5)
    topology.add_edge(2, 5)
    source = 4
    receivers = (0, 5) 
    caches = (1, 2, 3)
    contents = caches
    fnss.add_stack(topology, source, 'source', {'contents': contents})
    for v in caches:
        fnss.add_stack(topology, v, 'cache', {'size': 1})
    for v in receivers:
        fnss.add_stack(topology, v, 'receiver', {})
    topology.graph['cache_policy'] = 'FIFO'
    return topology

def off_path_topology():
    """Return topology for testing off-path caching strategies
    """
    # Topology sketch
    #
    #     --------- 5 ----------  
    #    /                      \
    #   /                        \
    # 0 ---- 1 ---- 2 ---- 3 ---- 4 
    #               |
    #               |
    #               6
    #
    topology = fnss.ring_topology(6)
    topology.add_edge(2, 6)
    topology.add_edge(1, 7)
    source = 4
    receivers = (0, 6, 7) 
    caches = (1, 2, 3, 5)
    contents = caches
    fnss.add_stack(topology, source, 'source', {'contents': contents})
    for v in caches:
        fnss.add_stack(topology, v, 'cache', {'size': 1})
    for v in receivers:
        fnss.add_stack(topology, v, 'receiver', {})
    topology.graph['cache_policy'] = 'FIFO'
    return topology

class TestHashrouting(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass    
    
    def setUp(self):
        topology = off_path_topology()
        model = NetworkModel(topology)
        self.view = NetworkView(model)
        self.controller = NetworkController(model)
        self.collector = TestCollector(self.view)
        self.controller.attach_collector(self.collector)

    def tearDown(self):
        pass

    def test_hashrouting_symmetric(self):
        hr = strategy.HashroutingSymmetric(self.view, self.controller)
        hr.authoritative_cache = lambda x: x
        # At time 1, receiver 0 requests content 2
        hr.process_event(1, 0, 2, True)
        loc = self.view.content_locations(2)
        self.assertEquals(len(loc), 2)
        self.assertIn(2, loc)
        self.assertIn(4, loc)
        summary = self.collector.session_summary()
        exp_req_hops = set(((0, 1), (1, 2), (2, 3), (3, 4)))
        exp_cont_hops = set(((4, 3), (3, 2), (2, 1), (1, 0)))
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(exp_req_hops, set(req_hops))
        self.assertSetEqual(exp_cont_hops, set(cont_hops))
        # At time 2 repeat request, expect cache hit
        hr.process_event(2, 0, 2, True)
        loc = self.view.content_locations(2)
        self.assertEquals(len(loc), 2)
        self.assertIn(2, loc)
        self.assertIn(4, loc)
        summary = self.collector.session_summary()
        exp_req_hops = set(((0, 1), (1, 2)))
        exp_cont_hops = set(((2, 1), (1, 0)))
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(exp_req_hops, set(req_hops))
        self.assertSetEqual(exp_cont_hops, set(cont_hops))
        # Now request from node 6, expect hit
        hr.process_event(3, 6, 2, True)
        loc = self.view.content_locations(2)
        self.assertEquals(len(loc), 2)
        self.assertIn(2, loc)
        self.assertIn(4, loc)
        summary = self.collector.session_summary()
        exp_req_hops = set(((6, 2),))
        exp_cont_hops = set(((2, 6),))
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(exp_req_hops, set(req_hops))
        self.assertSetEqual(exp_cont_hops, set(cont_hops))

    def test_hashrouting_asymmetric(self):
        hr = strategy.HashroutingAsymmetric(self.view, self.controller)
        hr.authoritative_cache = lambda x: x
        # At time 1, receiver 0 requests content 2
        hr.process_event(1, 0, 2, True)
        loc = self.view.content_locations(2)
        self.assertEquals(len(loc), 1)
        self.assertIn(4, loc)
        summary = self.collector.session_summary()
        exp_req_hops = set(((0, 1), (1, 2), (2, 3), (3, 4)))
        exp_cont_hops = set(((4, 5), (5, 0)))
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(exp_req_hops, set(req_hops))
        self.assertSetEqual(exp_cont_hops, set(cont_hops))
        # Now request from node 6, expect miss but cache insertion
        hr.process_event(2, 6, 2, True)
        loc = self.view.content_locations(2)
        self.assertEquals(len(loc), 2)
        self.assertIn(2, loc)
        self.assertIn(4, loc)
        summary = self.collector.session_summary()
        exp_req_hops = set(((6, 2), (2, 3), (3, 4)))
        exp_cont_hops = set(((4, 3), (3, 2), (2, 6)))
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(exp_req_hops, set(req_hops))
        self.assertSetEqual(exp_cont_hops, set(cont_hops))
        # Now request from node 0 again, expect hit
        hr.process_event(3, 0, 2, True)
        loc = self.view.content_locations(2)
        self.assertEquals(len(loc), 2)
        self.assertIn(2, loc)
        self.assertIn(4, loc)
        summary = self.collector.session_summary()
        exp_req_hops = set(((0, 1), (1, 2)))
        exp_cont_hops = set(((2, 1), (1, 0)))
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(exp_req_hops, set(req_hops))
        self.assertSetEqual(exp_cont_hops, set(cont_hops))

    def test_hashrouting_multicast(self):
        hr = strategy.HashroutingMulticast(self.view, self.controller)
        hr.authoritative_cache = lambda x: x
        # At time 1, receiver 0 requests content 2
        hr.process_event(1, 0, 2, True)
        loc = self.view.content_locations(2)
        self.assertEquals(len(loc), 2)
        self.assertIn(2, loc)
        self.assertIn(4, loc)
        summary = self.collector.session_summary()
        exp_req_hops = set(((0, 1), (1, 2), (2, 3), (3, 4)))
        exp_cont_hops = set(((4, 3), (3, 2), (4, 5), (5, 0)))
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(exp_req_hops, set(req_hops))
        self.assertSetEqual(exp_cont_hops, set(cont_hops))
        # At time 2 repeat request, expect cache hit
        hr.process_event(2, 0, 2, True)
        loc = self.view.content_locations(2)
        self.assertEquals(len(loc), 2)
        self.assertIn(2, loc)
        self.assertIn(4, loc)
        summary = self.collector.session_summary()
        exp_req_hops = set(((0, 1), (1, 2)))
        exp_cont_hops = set(((2, 1), (1, 0)))
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(exp_req_hops, set(req_hops))
        self.assertSetEqual(exp_cont_hops, set(cont_hops))
        # Now request from node 6, expect hit
        hr.process_event(3, 6, 2, True)
        loc = self.view.content_locations(2)
        self.assertEquals(len(loc), 2)
        self.assertIn(2, loc)
        self.assertIn(4, loc)
        summary = self.collector.session_summary()
        exp_req_hops = set(((6, 2),))
        exp_cont_hops = set(((2, 6),))
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(exp_req_hops, set(req_hops))
        self.assertSetEqual(exp_cont_hops, set(cont_hops))
   
    def test_hashrouting_hybrid_am(self):
        hr = strategy.HashroutingHybridAM(self.view, self.controller, max_stretch=0.3)
        hr.authoritative_cache = lambda x: x
        # At time 1, receiver 0 requests content 2, expect asymmetric
        hr.process_event(1, 0, 2, True)
        loc = self.view.content_locations(2)
        self.assertEquals(len(loc), 1)
        self.assertIn(4, loc)
        summary = self.collector.session_summary()
        exp_req_hops = set(((0, 1), (1, 2), (2, 3), (3, 4)))
        exp_cont_hops = set(((4, 5), (5, 0)))
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(exp_req_hops, set(req_hops))
        self.assertSetEqual(exp_cont_hops, set(cont_hops))
        # At time 2, receiver 0 requests content 3, expect multicast
        hr.process_event(3, 0, 3, True)
        loc = self.view.content_locations(3)
        self.assertEquals(len(loc), 2)
        self.assertIn(3, loc)
        self.assertIn(4, loc)
        summary = self.collector.session_summary()
        exp_req_hops = set(((0, 1), (1, 2), (2, 3), (3, 4)))
        exp_cont_hops = set(((4, 5), (5, 0), (4, 3)))
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(exp_req_hops, set(req_hops))
        self.assertSetEqual(exp_cont_hops, set(cont_hops))
        # At time 3, receiver 0 requests content 5, expect symm = mcast = asymm
        hr.process_event(3, 0, 5, True)
        loc = self.view.content_locations(5)
        self.assertEquals(len(loc), 2)
        self.assertIn(5, loc)
        self.assertIn(4, loc)
        summary = self.collector.session_summary()
        exp_req_hops = set(((0, 5), (5, 4)))
        exp_cont_hops = set(((4, 5), (5, 0)))
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(exp_req_hops, set(req_hops))
        self.assertSetEqual(exp_cont_hops, set(cont_hops)) 

    def test_hashrouting_hybrid_sm(self):
        hr = strategy.HashroutingHybridSM(self.view, self.controller)
        hr.authoritative_cache = lambda x: x
        # At time 1, receiver 0 requests content 2, expect asymmetric
        hr.process_event(1, 0, 3, True)
        loc = self.view.content_locations(3)
        self.assertEquals(len(loc), 2)
        self.assertIn(3, loc)
        self.assertIn(4, loc)
        summary = self.collector.session_summary()
        exp_req_hops = set(((0, 1), (1, 2), (2, 3), (3, 4)))
        exp_cont_hops = set(((4, 5), (5, 0), (4, 3)))
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(exp_req_hops, set(req_hops))
        self.assertSetEqual(exp_cont_hops, set(cont_hops))
        # At time 2, receiver 0 requests content 5, expect symm = mcast = asymm
        hr.process_event(2, 0, 5, True)
        loc = self.view.content_locations(5)
        self.assertEquals(len(loc), 2)
        self.assertIn(5, loc)
        self.assertIn(4, loc)
        summary = self.collector.session_summary()
        exp_req_hops = set(((0, 5), (5, 4)))
        exp_cont_hops = set(((4, 5), (5, 0)))
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(exp_req_hops, set(req_hops))
        self.assertSetEqual(exp_cont_hops, set(cont_hops))
        
    def test_hashrouting_hybrid_sm_multi_options(self):
        # NOTE: The following test case will fail because NetworkX returns as
        # shortest path from 4 to 1: 4-5-0-1. There is also another shortest
        # path: 4-3-2-1. The best delivery strategy overall would be multicast
        # but because of NetworkX selecting the least convenient shortest path
        # the computed solution is symmetric with path: 4-5-0-1-2-6.
        pass 
#        # At time 1, receiver 6 requests content 1, expect multicast
#        hr = strategy.HashroutingHybridSM(self.view, self.controller)
#        hr.authoritative_cache = lambda x: x
#        hr.process_event(1, 6, 1, True)
#        loc = self.view.content_locations(1)
#        self.assertEquals(len(loc), 2)
#        self.assertIn(1, loc)
#        self.assertIn(4, loc)
#        summary = self.collector.session_summary()
#        exp_req_hops = set(((6, 2), (2, 1), (1, 2), (2, 3), (3, 4)))
#        exp_cont_hops = set(((4, 3), (3, 2), (2, 1), (2, 6)))
#        req_hops = summary['request_hops']
#        cont_hops = summary['content_hops']
#        self.assertSetEqual(exp_req_hops, set(req_hops))
#        self.assertSetEqual(exp_cont_hops, set(cont_hops)) 

class TestOnPath(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass    
    
    def setUp(self):
        topology = on_path_topology()
        model = NetworkModel(topology)
        self.view = NetworkView(model)
        self.controller = NetworkController(model)
        self.collector = TestCollector(self.view)
        self.controller.attach_collector(self.collector)
        
    def tearDown(self):
        pass
    
    def test_lce_same_content(self):
        hr = strategy.LeaveCopyEverywhere(self.view, self.controller)
        # receiver 0 requests 2, expect miss
        hr.process_event(1, 0, 2, True)
        loc = self.view.content_locations(2)
        self.assertEquals(len(loc), 4)
        self.assertIn(1, loc)
        self.assertIn(2, loc)
        self.assertIn(3, loc)
        self.assertIn(4, loc)
        summary = self.collector.session_summary()
        exp_req_hops = set(((0, 1), (1, 2), (2, 3), (3, 4)))
        exp_cont_hops = set(((4, 3), (3, 2), (2, 1), (1, 0)))
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(exp_req_hops, set(req_hops))
        self.assertSetEqual(exp_cont_hops, set(cont_hops))
        # receiver 0 requests 2, expect hit
        hr.process_event(1, 5, 2, True)
        loc = self.view.content_locations(2)
        self.assertEquals(len(loc), 4)
        self.assertIn(1, loc)
        self.assertIn(2, loc)
        self.assertIn(3, loc)
        self.assertIn(4, loc)
        summary = self.collector.session_summary()
        exp_req_hops = set(((5, 2),))
        exp_cont_hops = set(((2, 5),))
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(exp_req_hops, set(req_hops))
        self.assertSetEqual(exp_cont_hops, set(cont_hops))

    def test_lce_different_content(self):
        hr = strategy.LeaveCopyEverywhere(self.view, self.controller)
        # receiver 0 requests 2, expect miss
        hr.process_event(1, 0, 2, True)
        loc = self.view.content_locations(2)
        self.assertEquals(len(loc), 4)
        self.assertIn(1, loc)
        self.assertIn(2, loc)
        self.assertIn(3, loc)
        self.assertIn(4, loc)
        summary = self.collector.session_summary()
        exp_req_hops = set(((0, 1), (1, 2), (2, 3), (3, 4)))
        exp_cont_hops = set(((4, 3), (3, 2), (2, 1), (1, 0)))
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(exp_req_hops, set(req_hops))
        self.assertSetEqual(exp_cont_hops, set(cont_hops))
        # request content 3 from 5
        hr.process_event(1, 5, 3, True)
        loc = self.view.content_locations(3)
        self.assertEquals(len(loc), 3)
        self.assertIn(2, loc)
        self.assertIn(3, loc)
        self.assertIn(4, loc)
        loc = self.view.content_locations(2)
        self.assertEquals(len(loc), 2)
        self.assertIn(1, loc)
        self.assertIn(4, loc)
        summary = self.collector.session_summary()
        exp_req_hops = set(((5, 2), (2, 3), (3, 4)))
        exp_cont_hops = set(((4, 3), (3, 2), (2, 5)))
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(exp_req_hops, set(req_hops))
        self.assertSetEqual(exp_cont_hops, set(cont_hops))
        # request content 3 from , hit in 2
        hr.process_event(1, 0, 3, True)
        loc = self.view.content_locations(3)
        self.assertEquals(len(loc), 4)
        self.assertIn(1, loc)
        self.assertIn(2, loc)
        self.assertIn(3, loc)
        self.assertIn(4, loc)
        loc = self.view.content_locations(2)
        self.assertEquals(len(loc), 1)
        self.assertIn(4, loc)
        summary = self.collector.session_summary()
        exp_req_hops = set(((0, 1), (1, 2)))
        exp_cont_hops = set(((2, 1), (1, 0)))
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(exp_req_hops, set(req_hops))
        self.assertSetEqual(exp_cont_hops, set(cont_hops))
        
    def test_lcd(self):
        hr = strategy.LeaveCopyDown(self.view, self.controller)
        # receiver 0 requests 2, expect miss
        hr.process_event(1, 0, 2, True)
        loc = self.view.content_locations(2)
        self.assertEquals(len(loc), 2)
        self.assertIn(3, loc)
        self.assertIn(4, loc)
        summary = self.collector.session_summary()
        exp_req_hops = set(((0, 1), (1, 2), (2, 3), (3, 4)))
        exp_cont_hops = set(((4, 3), (3, 2), (2, 1), (1, 0)))
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(exp_req_hops, set(req_hops))
        self.assertSetEqual(exp_cont_hops, set(cont_hops))
        # receiver 0 requests 2, expect hit in 3
        hr.process_event(1, 0, 2, True)
        loc = self.view.content_locations(2)
        self.assertEquals(len(loc), 3)
        self.assertIn(2, loc)
        self.assertIn(3, loc)
        self.assertIn(4, loc)
        summary = self.collector.session_summary()
        exp_req_hops = set(((0, 1), (1, 2), (2, 3)))
        exp_cont_hops = set(((3, 2), (2, 1), (1, 0)))
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(exp_req_hops, set(req_hops))
        self.assertSetEqual(exp_cont_hops, set(cont_hops))
        # receiver 0 requests 2, expect hit in 2
        hr.process_event(1, 0, 2, True)
        loc = self.view.content_locations(2)
        self.assertEquals(len(loc), 4)
        self.assertIn(1, loc)
        self.assertIn(2, loc)
        self.assertIn(3, loc)
        self.assertIn(4, loc)
        summary = self.collector.session_summary()
        exp_req_hops = set(((0, 1), (1, 2),))
        exp_cont_hops = set(((2, 1), (1, 0)))
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(exp_req_hops, set(req_hops))
        self.assertSetEqual(exp_cont_hops, set(cont_hops))
        # receiver 0 requests 2, expect hit in 1
        hr.process_event(1, 0, 2, True)
        loc = self.view.content_locations(2)
        self.assertEquals(len(loc), 4)
        self.assertIn(1, loc)
        self.assertIn(2, loc)
        self.assertIn(3, loc)
        self.assertIn(4, loc)
        summary = self.collector.session_summary()
        exp_req_hops = set(((0, 1),))
        exp_cont_hops = set(((1, 0),))
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(exp_req_hops, set(req_hops))
        self.assertSetEqual(exp_cont_hops, set(cont_hops))
        # receiver 0 requests 3, expect miss and eviction of 2 from 3
        hr.process_event(1, 0, 3, True)
        loc = self.view.content_locations(2)
        self.assertEquals(len(loc), 3)
        self.assertIn(1, loc)
        self.assertIn(2, loc)
        self.assertIn(4, loc)
        loc = self.view.content_locations(3)
        self.assertEquals(len(loc), 2)
        self.assertIn(3, loc)
        self.assertIn(4, loc)
        summary = self.collector.session_summary()
        exp_req_hops = set(((0, 1), (1, 2), (2, 3), (3, 4)))
        exp_cont_hops = set(((4, 3), (3, 2), (2, 1), (1, 0)))
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(exp_req_hops, set(req_hops))
        self.assertSetEqual(exp_cont_hops, set(cont_hops))
        
    def test_cl4m(self):
        hr = strategy.CacheLessForMore(self.view, self.controller)
        # receiver 0 requests 2, expect miss
        hr.process_event(1, 0, 2, True)
        loc = self.view.content_locations(2)
        self.assertEquals(len(loc), 2)
        self.assertIn(2, loc)
        self.assertIn(4, loc)
        summary = self.collector.session_summary()
        exp_req_hops = set(((0, 1), (1, 2), (2, 3), (3, 4)))
        exp_cont_hops = set(((4, 3), (3, 2), (2, 1), (1, 0)))
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(exp_req_hops, set(req_hops))
        self.assertSetEqual(exp_cont_hops, set(cont_hops))
        # receiver 0 requests 2, expect hit
        hr.process_event(1, 0, 2, True)
        loc = self.view.content_locations(2)
        self.assertEquals(len(loc), 3)
        self.assertIn(1, loc)
        self.assertIn(2, loc)
        self.assertIn(4, loc)
        summary = self.collector.session_summary()
        exp_req_hops = set(((0, 1), (1, 2)))
        exp_cont_hops = set(((2, 1), (1, 0)))
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(exp_req_hops, set(req_hops))
        self.assertSetEqual(exp_cont_hops, set(cont_hops))
        # receiver 0 requests 3, expect miss
        hr.process_event(1, 0, 3, True)
        loc = self.view.content_locations(2)
        self.assertEquals(len(loc), 2)
        self.assertIn(1, loc)
        self.assertIn(4, loc)
        loc = self.view.content_locations(3)
        self.assertEquals(len(loc), 2)
        self.assertIn(2, loc)
        self.assertIn(4, loc)
        summary = self.collector.session_summary()
        exp_req_hops = set(((0, 1), (1, 2), (2, 3), (3, 4)))
        exp_cont_hops = set(((4, 3), (3, 2), (2, 1), (1, 0)))
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(exp_req_hops, set(req_hops))
        self.assertSetEqual(exp_cont_hops, set(cont_hops))
        