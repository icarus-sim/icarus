import unittest

import fnss

from icarus.scenarios import IcnTopology
import icarus.models as strategy
from icarus.execution import NetworkModel, NetworkView, NetworkController, DummyCollector


class TestHashroutingEdge(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    @classmethod
    def topology(cls):
        #
        #              4
        #           /     \
        #  r ---- 1 -- 2 -- 3 ---- s
        #
        topology = IcnTopology()
        topology.add_path(["r", 1, 2, 3, "s"])
        topology.add_path([1, 4, 3])
        fnss.add_stack(topology, "r", "receiver")
        fnss.add_stack(topology, "s", "source", {'contents': range(1, 61)})
        for v in (1, 2, 3, 4):
            fnss.add_stack(topology, v, "router", {"cache_size": 4})
        topology.graph['icr_candidates'] = set([1, 2, 3, 4])
        return topology

    def setUp(self):
        topology = self.topology()
        model = NetworkModel(topology, cache_policy={'name': 'FIFO'})
        self.view = NetworkView(model)
        self.controller = NetworkController(model)
        self.collector = DummyCollector(self.view)
        self.controller.attach_collector(self.collector)

    def tearDown(self):
        pass

    def test_hashrouting_symmetric_edge(self):
        hr = strategy.HashroutingEdge(self.view, self.controller, 'SYMM', 0.25)
        hr.authoritative_cache = lambda x: ((x - 1) % 4) + 1
        # At time 1, request content 4
        hr.process_event(1, "r", 4, True)
        loc = self.view.content_locations(4)
        self.assertIn("s", loc)
        self.assertIn(4, loc)
        self.assertTrue(self.view.local_cache_lookup(1, 4))
        self.assertFalse(self.view.local_cache_lookup(2, 4))
        self.assertFalse(self.view.local_cache_lookup(3, 4))
        summary = self.collector.session_summary()
        exp_req_hops = [("r", 1), (1, 4), (4, 3), (3, "s")]
        exp_cont_hops = [("s", 3), (3, 4), (4, 1), (1, "r")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(set(exp_req_hops), set(req_hops))
        self.assertSetEqual(set(exp_cont_hops), set(cont_hops))
        self.assertEqual("s", summary['serving_node'])
        # Let's request it again to make sure we have hit from edge cache
        hr.process_event(1, "r", 4, True)
        loc = self.view.content_locations(4)
        self.assertIn("s", loc)
        self.assertIn(4, loc)
        self.assertTrue(self.view.local_cache_lookup(1, 4))
        self.assertFalse(self.view.local_cache_lookup(2, 4))
        self.assertFalse(self.view.local_cache_lookup(3, 4))
        summary = self.collector.session_summary()
        exp_req_hops = [("r", 1)]
        exp_cont_hops = [(1, "r")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(set(exp_req_hops), set(req_hops))
        self.assertSetEqual(set(exp_cont_hops), set(cont_hops))
        self.assertEqual(1, summary['serving_node'])
        # Now request content 6 which should replace 4 in the local cache of 1
        # but not 3, because 6 would take space in 3's coordinated ratio
        hr.process_event(1, "r", 7, True)
        loc = self.view.content_locations(7)
        self.assertIn("s", loc)
        self.assertIn(3, loc)
        self.assertTrue(self.view.local_cache_lookup(1, 7))
        self.assertFalse(self.view.local_cache_lookup(2, 7))
        self.assertFalse(self.view.local_cache_lookup(3, 7))
        summary = self.collector.session_summary()
        exp_req_hops = [("r", 1), (1, 2), (2, 3), (3, "s")]
        exp_cont_hops = [("s", 3), (3, 2), (2, 1), (1, "r")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(set(exp_req_hops), set(req_hops))
        self.assertSetEqual(set(exp_cont_hops), set(cont_hops))
        self.assertEqual("s", summary['serving_node'])
        # Verify where 4 is still stored
        self.assertFalse(self.view.local_cache_lookup(1, 4))
        self.assertFalse(self.view.local_cache_lookup(2, 4))
        self.assertFalse(self.view.local_cache_lookup(3, 4))
        # Request again 4
        hr.process_event(1, "r", 4, True)
        loc = self.view.content_locations(4)
        self.assertIn("s", loc)
        self.assertIn(4, loc)
        self.assertTrue(self.view.local_cache_lookup(1, 4))
        self.assertFalse(self.view.local_cache_lookup(2, 4))
        self.assertFalse(self.view.local_cache_lookup(3, 4))
        summary = self.collector.session_summary()
        exp_req_hops = [("r", 1), (1, 4)]
        exp_cont_hops = [(4, 1), (1, "r")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(set(exp_req_hops), set(req_hops))
        self.assertSetEqual(set(exp_cont_hops), set(cont_hops))
        self.assertEqual(4, summary['serving_node'])


    def test_hashrouting_symmetric_edge_zero_local(self):
        hr = strategy.HashroutingEdge(self.view, self.controller, 'SYMM', 0)
        hr.authoritative_cache = lambda x: ((x - 1) % 4) + 1
        # At time 1, request content 4
        hr.process_event(1, "r", 4, True)
        loc = self.view.content_locations(4)
        self.assertIn("s", loc)
        self.assertIn(4, loc)
        self.assertFalse(self.view.local_cache_lookup(1, 4))
        self.assertFalse(self.view.local_cache_lookup(2, 4))
        self.assertFalse(self.view.local_cache_lookup(3, 4))
        summary = self.collector.session_summary()
        exp_req_hops = [("r", 1), (1, 4), (4, 3), (3, "s")]
        exp_cont_hops = [("s", 3), (3, 4), (4, 1), (1, "r")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(set(exp_req_hops), set(req_hops))
        self.assertSetEqual(set(exp_cont_hops), set(cont_hops))
        self.assertEqual("s", summary['serving_node'])
        # Let's request it again to make sure we have hit from edge cache
        hr.process_event(1, "r", 4, True)
        loc = self.view.content_locations(4)
        self.assertIn("s", loc)
        self.assertIn(4, loc)
        self.assertFalse(self.view.local_cache_lookup(1, 4))
        self.assertFalse(self.view.local_cache_lookup(2, 4))
        self.assertFalse(self.view.local_cache_lookup(3, 4))
        summary = self.collector.session_summary()
        exp_req_hops = [("r", 1), (1, 4)]
        exp_cont_hops = [(4, 1), (1, "r")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(set(exp_req_hops), set(req_hops))
        self.assertSetEqual(set(exp_cont_hops), set(cont_hops))
        self.assertEqual(4, summary['serving_node'])
        # Now request content 6 which should replace 4 in the local cache of 1
        # but not 3, because 6 would take space in 3's coordinated ratio
        hr.process_event(1, "r", 7, True)
        loc = self.view.content_locations(7)
        self.assertIn("s", loc)
        self.assertIn(3, loc)
        self.assertFalse(self.view.local_cache_lookup(1, 7))
        self.assertFalse(self.view.local_cache_lookup(2, 7))
        self.assertFalse(self.view.local_cache_lookup(3, 7))
        summary = self.collector.session_summary()
        exp_req_hops = [("r", 1), (1, 2), (2, 3), (3, "s")]
        exp_cont_hops = [("s", 3), (3, 2), (2, 1), (1, "r")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(set(exp_req_hops), set(req_hops))
        self.assertSetEqual(set(exp_cont_hops), set(cont_hops))
        self.assertEqual("s", summary['serving_node'])
        # Verify where 4 is still stored
        self.assertFalse(self.view.local_cache_lookup(1, 4))
        self.assertFalse(self.view.local_cache_lookup(2, 4))
        self.assertFalse(self.view.local_cache_lookup(3, 4))
        # Request again 4
        hr.process_event(1, "r", 4, True)
        loc = self.view.content_locations(4)
        self.assertIn("s", loc)
        self.assertIn(4, loc)
        self.assertFalse(self.view.local_cache_lookup(1, 4))
        self.assertFalse(self.view.local_cache_lookup(2, 4))
        self.assertFalse(self.view.local_cache_lookup(3, 4))
        summary = self.collector.session_summary()
        exp_req_hops = [("r", 1), (1, 4)]
        exp_cont_hops = [(4, 1), (1, "r")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(set(exp_req_hops), set(req_hops))
        self.assertSetEqual(set(exp_cont_hops), set(cont_hops))
        self.assertEqual(4, summary['serving_node'])


    def test_hashrouting_symmetric_edge_zero_coordinated(self):
        hr = strategy.HashroutingEdge(self.view, self.controller, 'SYMM', 1)
        hr.authoritative_cache = lambda x: ((x - 1) % 4) + 1
        # At time 1, request content 4
        hr.process_event(1, "r", 4, True)
        loc = self.view.content_locations(4)
        self.assertIn("s", loc)
        self.assertNotIn(4, loc)
        self.assertTrue(self.view.local_cache_lookup(1, 4))
        self.assertFalse(self.view.local_cache_lookup(2, 4))
        self.assertFalse(self.view.local_cache_lookup(3, 4))
        summary = self.collector.session_summary()
        exp_req_hops = [("r", 1), (1, 4), (4, 3), (3, "s")]
        exp_cont_hops = [("s", 3), (3, 4), (4, 1), (1, "r")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(set(exp_req_hops), set(req_hops))
        self.assertSetEqual(set(exp_cont_hops), set(cont_hops))
        self.assertEqual("s", summary['serving_node'])
        # Let's request it again to make sure we have hit from edge cache
        hr.process_event(1, "r", 4, True)
        loc = self.view.content_locations(4)
        self.assertIn("s", loc)
        self.assertNotIn(4, loc)
        self.assertTrue(self.view.local_cache_lookup(1, 4))
        self.assertFalse(self.view.local_cache_lookup(2, 4))
        self.assertFalse(self.view.local_cache_lookup(3, 4))
        summary = self.collector.session_summary()
        exp_req_hops = [("r", 1)]
        exp_cont_hops = [(1, "r")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(set(exp_req_hops), set(req_hops))
        self.assertSetEqual(set(exp_cont_hops), set(cont_hops))
        self.assertEqual(1, summary['serving_node'])
        # Now request content 6 which should replace 4 in the local cache of 1
        # but not 3, because 6 would take space in 3's coordinated ratio
        hr.process_event(1, "r", 7, True)
        loc = self.view.content_locations(7)
        self.assertIn("s", loc)
        self.assertNotIn(3, loc)
        self.assertTrue(self.view.local_cache_lookup(1, 7))
        self.assertFalse(self.view.local_cache_lookup(2, 7))
        self.assertFalse(self.view.local_cache_lookup(3, 7))
        summary = self.collector.session_summary()
        exp_req_hops = [("r", 1), (1, 2), (2, 3), (3, "s")]
        exp_cont_hops = [("s", 3), (3, 2), (2, 1), (1, "r")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(set(exp_req_hops), set(req_hops))
        self.assertSetEqual(set(exp_cont_hops), set(cont_hops))
        self.assertEqual("s", summary['serving_node'])
        # Verify where 4 is still stored
        self.assertTrue(self.view.local_cache_lookup(1, 4))
        self.assertFalse(self.view.local_cache_lookup(2, 4))
        self.assertFalse(self.view.local_cache_lookup(3, 4))
        # Request again 4
        hr.process_event(1, "r", 4, True)
        loc = self.view.content_locations(4)
        self.assertIn("s", loc)
        self.assertNotIn(4, loc)
        self.assertTrue(self.view.local_cache_lookup(1, 4))
        self.assertFalse(self.view.local_cache_lookup(2, 4))
        self.assertFalse(self.view.local_cache_lookup(3, 4))
        summary = self.collector.session_summary()
        exp_req_hops = [("r", 1)]
        exp_cont_hops = [(1, "r")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(set(exp_req_hops), set(req_hops))
        self.assertSetEqual(set(exp_cont_hops), set(cont_hops))
        self.assertEqual(1, summary['serving_node'])


class TestHashroutingOnPath(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    @classmethod
    def topology(cls):
        #
        #              4
        #           /     \
        #  r ---- 1 -- 2 -- 3 ---- s
        #
        topology = IcnTopology()
        topology.add_path(["r", 1, 2, 3, "s"])
        topology.add_path([1, 4, 3])
        fnss.add_stack(topology, "r", "receiver")
        fnss.add_stack(topology, "s", "source", {'contents': range(1, 61)})
        for v in (1, 2, 3, 4):
            fnss.add_stack(topology, v, "router", {"cache_size": 4})
        topology.graph['icr_candidates'] = set([1, 2, 3, 4])
        return topology

    def setUp(self):
        topology = self.topology()
        model = NetworkModel(topology, cache_policy={'name': 'FIFO'})
        self.view = NetworkView(model)
        self.controller = NetworkController(model)
        self.collector = DummyCollector(self.view)
        self.controller.attach_collector(self.collector)

    def tearDown(self):
        pass

    def test_hashrouting_symmetric(self):
        hr = strategy.HashroutingOnPath(self.view, self.controller, 'SYMM', 0.25)
        hr.authoritative_cache = lambda x: ((x - 1) % 4) + 1
        # At time 1, request content 4
        hr.process_event(1, "r", 4, True)
        loc = self.view.content_locations(4)
        self.assertIn("s", loc)
        self.assertIn(4, loc)
        self.assertTrue(self.view.local_cache_lookup(1, 4))
        self.assertFalse(self.view.local_cache_lookup(2, 4))
        self.assertTrue(self.view.local_cache_lookup(3, 4))
        summary = self.collector.session_summary()
        exp_req_hops = [("r", 1), (1, 4), (4, 3), (3, "s")]
        exp_cont_hops = [("s", 3), (3, 4), (4, 1), (1, "r")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(set(exp_req_hops), set(req_hops))
        self.assertSetEqual(set(exp_cont_hops), set(cont_hops))
        self.assertEqual("s", summary['serving_node'])
        # Let's request it again to make sure we have hit from edge cache
        hr.process_event(1, "r", 4, True)
        loc = self.view.content_locations(4)
        self.assertIn("s", loc)
        self.assertIn(4, loc)
        self.assertTrue(self.view.local_cache_lookup(1, 4))
        self.assertFalse(self.view.local_cache_lookup(2, 4))
        self.assertTrue(self.view.local_cache_lookup(3, 4))
        summary = self.collector.session_summary()
        exp_req_hops = [("r", 1)]
        exp_cont_hops = [(1, "r")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(set(exp_req_hops), set(req_hops))
        self.assertSetEqual(set(exp_cont_hops), set(cont_hops))
        self.assertEqual(1, summary['serving_node'])
        # Now request content 7 which should replace 4 in the local cache of 1
        # but not 3, because 7 would take space in 3's coordinated ratio
        hr.process_event(1, "r", 7, True)
        loc = self.view.content_locations(7)
        self.assertIn("s", loc)
        self.assertIn(3, loc)
        self.assertTrue(self.view.local_cache_lookup(1, 7))
        self.assertTrue(self.view.local_cache_lookup(2, 7))
        self.assertFalse(self.view.local_cache_lookup(3, 7))
        summary = self.collector.session_summary()
        exp_req_hops = [("r", 1), (1, 2), (2, 3), (3, "s")]
        exp_cont_hops = [("s", 3), (3, 2), (2, 1), (1, "r")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(set(exp_req_hops), set(req_hops))
        self.assertSetEqual(set(exp_cont_hops), set(cont_hops))
        self.assertEqual("s", summary['serving_node'])
        # Verify where 4 is still stored
        self.assertFalse(self.view.local_cache_lookup(1, 4))
        self.assertFalse(self.view.local_cache_lookup(2, 4))
        self.assertTrue(self.view.local_cache_lookup(3, 4))
        # Request again 4
        hr.process_event(1, "r", 4, True)
        loc = self.view.content_locations(4)
        self.assertIn("s", loc)
        self.assertIn(4, loc)
        self.assertTrue(self.view.local_cache_lookup(1, 4))
        self.assertFalse(self.view.local_cache_lookup(2, 4))
        self.assertTrue(self.view.local_cache_lookup(3, 4))
        summary = self.collector.session_summary()
        exp_req_hops = [("r", 1), (1, 4)]
        exp_cont_hops = [(4, 1), (1, "r")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(set(exp_req_hops), set(req_hops))
        self.assertSetEqual(set(exp_cont_hops), set(cont_hops))
        self.assertEqual(4, summary['serving_node'])


    def test_hashrouting_symmetric_zero_local(self):
        hr = strategy.HashroutingOnPath(self.view, self.controller, 'SYMM', 0)
        hr.authoritative_cache = lambda x: ((x - 1) % 4) + 1
        # At time 1, request content 4
        hr.process_event(1, "r", 4, True)
        loc = self.view.content_locations(4)
        self.assertIn("s", loc)
        self.assertIn(4, loc)
        self.assertFalse(self.view.local_cache_lookup(1, 4))
        self.assertFalse(self.view.local_cache_lookup(2, 4))
        self.assertFalse(self.view.local_cache_lookup(3, 4))
        summary = self.collector.session_summary()
        exp_req_hops = [("r", 1), (1, 4), (4, 3), (3, "s")]
        exp_cont_hops = [("s", 3), (3, 4), (4, 1), (1, "r")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(set(exp_req_hops), set(req_hops))
        self.assertSetEqual(set(exp_cont_hops), set(cont_hops))
        self.assertEqual("s", summary['serving_node'])
        # Let's request it again to make sure we have hit from edge cache
        hr.process_event(1, "r", 4, True)
        loc = self.view.content_locations(4)
        self.assertIn("s", loc)
        self.assertIn(4, loc)
        self.assertFalse(self.view.local_cache_lookup(1, 4))
        self.assertFalse(self.view.local_cache_lookup(2, 4))
        self.assertFalse(self.view.local_cache_lookup(3, 4))
        summary = self.collector.session_summary()
        exp_req_hops = [("r", 1), (1, 4)]
        exp_cont_hops = [(4, 1), (1, "r")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(set(exp_req_hops), set(req_hops))
        self.assertSetEqual(set(exp_cont_hops), set(cont_hops))
        self.assertEqual(4, summary['serving_node'])
        # Now request content 6 which should replace 4 in the local cache of 1
        # but not 3, because 6 would take space in 3's coordinated ratio
        hr.process_event(1, "r", 7, True)
        loc = self.view.content_locations(7)
        self.assertIn("s", loc)
        self.assertIn(3, loc)
        self.assertFalse(self.view.local_cache_lookup(1, 7))
        self.assertFalse(self.view.local_cache_lookup(2, 7))
        self.assertFalse(self.view.local_cache_lookup(3, 7))
        summary = self.collector.session_summary()
        exp_req_hops = [("r", 1), (1, 2), (2, 3), (3, "s")]
        exp_cont_hops = [("s", 3), (3, 2), (2, 1), (1, "r")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(set(exp_req_hops), set(req_hops))
        self.assertSetEqual(set(exp_cont_hops), set(cont_hops))
        self.assertEqual("s", summary['serving_node'])
        # Verify where 4 is still stored
        self.assertFalse(self.view.local_cache_lookup(1, 4))
        self.assertFalse(self.view.local_cache_lookup(2, 4))
        self.assertFalse(self.view.local_cache_lookup(3, 4))
        # Request again 4
        hr.process_event(1, "r", 4, True)
        loc = self.view.content_locations(4)
        self.assertIn("s", loc)
        self.assertIn(4, loc)
        self.assertFalse(self.view.local_cache_lookup(1, 4))
        self.assertFalse(self.view.local_cache_lookup(2, 4))
        self.assertFalse(self.view.local_cache_lookup(3, 4))
        summary = self.collector.session_summary()
        exp_req_hops = [("r", 1), (1, 4)]
        exp_cont_hops = [(4, 1), (1, "r")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(set(exp_req_hops), set(req_hops))
        self.assertSetEqual(set(exp_cont_hops), set(cont_hops))
        self.assertEqual(4, summary['serving_node'])


    def test_hashrouting_symmetric_zero_coordinated(self):
        hr = strategy.HashroutingOnPath(self.view, self.controller, 'SYMM', 1)
        hr.authoritative_cache = lambda x: ((x - 1) % 4) + 1
        # At time 1, request content 4
        hr.process_event(1, "r", 4, True)
        loc = self.view.content_locations(4)
        self.assertIn("s", loc)
        self.assertNotIn(4, loc)
        self.assertTrue(self.view.local_cache_lookup(1, 4))
        self.assertFalse(self.view.local_cache_lookup(2, 4))
        self.assertTrue(self.view.local_cache_lookup(3, 4))
        summary = self.collector.session_summary()
        exp_req_hops = [("r", 1), (1, 4), (4, 3), (3, "s")]
        exp_cont_hops = [("s", 3), (3, 4), (4, 1), (1, "r")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(set(exp_req_hops), set(req_hops))
        self.assertSetEqual(set(exp_cont_hops), set(cont_hops))
        self.assertEqual("s", summary['serving_node'])
        # Let's request it again to make sure we have hit from edge cache
        hr.process_event(1, "r", 4, True)
        loc = self.view.content_locations(4)
        self.assertIn("s", loc)
        self.assertNotIn(4, loc)
        self.assertTrue(self.view.local_cache_lookup(1, 4))
        self.assertFalse(self.view.local_cache_lookup(2, 4))
        self.assertTrue(self.view.local_cache_lookup(3, 4))
        summary = self.collector.session_summary()
        exp_req_hops = [("r", 1)]
        exp_cont_hops = [(1, "r")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(set(exp_req_hops), set(req_hops))
        self.assertSetEqual(set(exp_cont_hops), set(cont_hops))
        self.assertEqual(1, summary['serving_node'])
        # Now request content 6 which should replace 4 in the local cache of 1
        # but not 3, because 6 would take space in 3's coordinated ratio
        hr.process_event(1, "r", 7, True)
        loc = self.view.content_locations(7)
        self.assertIn("s", loc)
        self.assertNotIn(3, loc)
        self.assertTrue(self.view.local_cache_lookup(1, 7))
        self.assertTrue(self.view.local_cache_lookup(2, 7))
        # Note: this assertion below is false, because we never store items
        # for the authoritative cache in the uncoordinated section, even if
        # the coordinated cache is empty
        self.assertFalse(self.view.local_cache_lookup(3, 7))
        summary = self.collector.session_summary()
        exp_req_hops = [("r", 1), (1, 2), (2, 3), (3, "s")]
        exp_cont_hops = [("s", 3), (3, 2), (2, 1), (1, "r")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(set(exp_req_hops), set(req_hops))
        self.assertSetEqual(set(exp_cont_hops), set(cont_hops))
        self.assertEqual("s", summary['serving_node'])
        # Verify where 4 is still stored
        self.assertTrue(self.view.local_cache_lookup(1, 4))
        self.assertFalse(self.view.local_cache_lookup(2, 4))
        self.assertTrue(self.view.local_cache_lookup(3, 4))
        # Request again 4
        hr.process_event(1, "r", 4, True)
        loc = self.view.content_locations(4)
        self.assertIn("s", loc)
        self.assertNotIn(4, loc)
        self.assertTrue(self.view.local_cache_lookup(1, 4))
        self.assertFalse(self.view.local_cache_lookup(2, 4))
        self.assertTrue(self.view.local_cache_lookup(3, 4))
        summary = self.collector.session_summary()
        exp_req_hops = [("r", 1)]
        exp_cont_hops = [(1, "r")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(set(exp_req_hops), set(req_hops))
        self.assertSetEqual(set(exp_cont_hops), set(cont_hops))
        self.assertEqual(1, summary['serving_node'])


class TestHashroutingClustered(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    @classmethod
    def clustered_topology(cls):
        """Return topology for testing off-path caching strategies
        """
        # Topology sketch
        #
        #             3                         6
        #            /  \                      /  \
        #           /    \                    /    \
        # RCV ---- 1 ---- 2 -[HIGH_DELAY]--- 4 ---- 5 ---- SRC
        #
        topology = IcnTopology()
        topology.add_path(['RCV', 1, 2, 4, 5, 'SRC'])
        topology.add_path([2, 3, 1])
        topology.add_path([5, 6, 4])
        fnss.set_delays_constant(topology, 1, 'ms')
        fnss.set_delays_constant(topology, 15, 'ms', [(2, 4)])
        caches = (1, 2, 3, 4, 5, 6)
        contents = [1, 2, 3]
        clusters = [set([1, 2, 3]), set([4, 5, 6])]
        topology.graph['icr_candidates'] = set(caches)
        topology.graph['clusters'] = clusters
        fnss.add_stack(topology, "RCV", 'receiver', {})
        topology.node["RCV"]["cluster"] = 0
        fnss.add_stack(topology, "SRC", 'source', {'contents': contents})
        topology.node["SRC"]["cluster"] = 1
        for v in caches:
            fnss.add_stack(topology, v, 'router', {'cache_size': 1})
            topology.node[v]["cluster"] = (v - 1) // 3
        return topology

    def setUp(self):
        topology = self.clustered_topology()
        self.model = NetworkModel(topology, cache_policy={'name': 'FIFO'})
        self.view = NetworkView(self.model)
        self.controller = NetworkController(self.model)
        self.collector = DummyCollector(self.view)
        self.controller.attach_collector(self.collector)

    def tearDown(self):
        pass


    def test_hashrouting_symmetric_lce(self):
        hr = strategy.HashroutingClustered(self.view, self.controller,
                                           intra_routing='SYMM',
                                           inter_routing='LCE')
        hr.authoritative_cache = lambda x, cluster: cluster * 3 + x
        # At time 1, receiver 0 requests content 2
        hr.process_event(1, "RCV", 3, True)
        loc = self.view.content_locations(3)
        self.assertEquals(len(loc), 3)
        self.assertIn("SRC", loc)
        self.assertIn(3, loc)
        self.assertIn(6, loc)
        summary = self.collector.session_summary()
        exp_req_hops = [("RCV", 1), (1, 3), (3, 2), (2, 4), (4, 6), (6, 5), (5, "SRC")]
        exp_cont_hops = [("SRC", 5), (5, 6), (6, 4), (4, 2), (2, 3), (3, 1), (1, "RCV")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(set(exp_req_hops), set(req_hops))
        self.assertSetEqual(set(exp_cont_hops), set(cont_hops))
        self.assertEqual(summary['serving_node'], "SRC")
        # Expect hit from first cluster
        hr.process_event(1, "RCV", 3, True)
        loc = self.view.content_locations(3)
        self.assertEquals(len(loc), 3)
        self.assertIn("SRC", loc)
        self.assertIn(3, loc)
        self.assertIn(6, loc)
        summary = self.collector.session_summary()
        exp_req_hops = [("RCV", 1), (1, 3)]
        exp_cont_hops = [(3, 1), (1, "RCV")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(set(exp_req_hops), set(req_hops))
        self.assertSetEqual(set(exp_cont_hops), set(cont_hops))
        self.assertEqual(summary['serving_node'], 3)
        # Delete entry on first cluster, expect hit on second cluster
        self.model.cache[3].remove(3)
        hr.process_event(1, "RCV", 3, True)
        loc = self.view.content_locations(3)
        self.assertEquals(len(loc), 3)
        self.assertIn("SRC", loc)
        self.assertIn(3, loc)
        self.assertIn(6, loc)
        summary = self.collector.session_summary()
        exp_req_hops = [("RCV", 1), (1, 3), (3, 2), (2, 4), (4, 6)]
        exp_cont_hops = [(6, 4), (4, 2), (2, 3), (3, 1), (1, "RCV")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(set(exp_req_hops), set(req_hops))
        self.assertSetEqual(set(exp_cont_hops), set(cont_hops))
        self.assertEqual(summary['serving_node'], 6)

    def test_hashrouting_asymmetric_lce(self):
        hr = strategy.HashroutingClustered(self.view, self.controller,
                                           intra_routing='ASYMM',
                                           inter_routing='LCE')
        hr.authoritative_cache = lambda x, cluster: cluster * 3 + x
        # Expect miss
        hr.process_event(1, "RCV", 3, True)
        loc = self.view.content_locations(3)
        self.assertEquals(len(loc), 1)
        self.assertIn("SRC", loc)
        self.assertNotIn(3, loc)
        self.assertNotIn(6, loc)
        summary = self.collector.session_summary()
        exp_req_hops = [("RCV", 1), (1, 3), (3, 2), (2, 4), (4, 6), (6, 5), (5, "SRC")]
        exp_cont_hops = [("SRC", 5), (5, 4), (4, 2), (2, 1), (1, "RCV")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(set(exp_req_hops), set(req_hops))
        self.assertSetEqual(set(exp_cont_hops), set(cont_hops))
        self.assertEqual(summary['serving_node'], "SRC")
        # Expect miss again, but this time caches will be populated
        hr.process_event(1, "RCV", 2, True)
        loc = self.view.content_locations(2)
        self.assertEquals(len(loc), 3)
        self.assertIn("SRC", loc)
        self.assertIn(2, loc)
        self.assertIn(5, loc)
        summary = self.collector.session_summary()
        exp_req_hops = [("RCV", 1), (1, 2), (2, 4), (4, 5), (5, 'SRC')]
        exp_cont_hops = [("SRC", 5), (5, 4), (4, 2), (2, 1), (1, "RCV")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(set(exp_req_hops), set(req_hops))
        self.assertSetEqual(set(exp_cont_hops), set(cont_hops))
        self.assertEqual(summary['serving_node'], "SRC")
        # Expect hit
        hr.process_event(1, "RCV", 2, True)
        loc = self.view.content_locations(2)
        self.assertEquals(len(loc), 3)
        self.assertIn("SRC", loc)
        self.assertIn(2, loc)
        self.assertIn(5, loc)
        summary = self.collector.session_summary()
        exp_req_hops = [("RCV", 1), (1, 2)]
        exp_cont_hops = [(2, 1), (1, "RCV")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(set(exp_req_hops), set(req_hops))
        self.assertSetEqual(set(exp_cont_hops), set(cont_hops))
        self.assertEqual(summary['serving_node'], 2)

    def test_hashrouting_multicast_lce(self):
        hr = strategy.HashroutingClustered(self.view, self.controller,
                                           intra_routing='MULTICAST',
                                           inter_routing='LCE')
        hr.authoritative_cache = lambda x, cluster: cluster * 3 + x
        # At time 1, receiver 0 requests content 2
        hr.process_event(1, "RCV", 3, True)
        loc = self.view.content_locations(3)
        self.assertEquals(len(loc), 3)
        self.assertIn("SRC", loc)
        self.assertIn(3, loc)
        self.assertIn(6, loc)
        summary = self.collector.session_summary()
        exp_req_hops = [("RCV", 1), (1, 3), (3, 2), (2, 4), (4, 6), (6, 5), (5, "SRC")]
        exp_cont_hops = [("SRC", 5), (5, 6), (5, 4), (4, 2), (2, 3), (2, 1), (1, "RCV")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(set(exp_req_hops), set(req_hops))
        self.assertSetEqual(set(exp_cont_hops), set(cont_hops))
        self.assertEqual(summary['serving_node'], "SRC")
        # Expect hit from first cluster
        hr.process_event(1, "RCV", 3, True)
        loc = self.view.content_locations(3)
        self.assertEquals(len(loc), 3)
        self.assertIn("SRC", loc)
        self.assertIn(3, loc)
        self.assertIn(6, loc)
        summary = self.collector.session_summary()
        exp_req_hops = [("RCV", 1), (1, 3)]
        exp_cont_hops = [(3, 1), (1, "RCV")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(set(exp_req_hops), set(req_hops))
        self.assertSetEqual(set(exp_cont_hops), set(cont_hops))
        self.assertEqual(summary['serving_node'], 3)
        # Delete entry on first cluster, expect hit on second cluster
        self.model.cache[3].remove(3)
        hr.process_event(1, "RCV", 3, True)
        loc = self.view.content_locations(3)
        self.assertEquals(len(loc), 3)
        self.assertIn("SRC", loc)
        self.assertIn(3, loc)
        self.assertIn(6, loc)
        summary = self.collector.session_summary()
        exp_req_hops = [("RCV", 1), (1, 3), (3, 2), (2, 4), (4, 6)]
        exp_cont_hops = [(6, 4), (4, 2), (2, 3), (2, 1), (1, "RCV")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(set(exp_req_hops), set(req_hops))
        self.assertSetEqual(set(exp_cont_hops), set(cont_hops))
        self.assertEqual(summary['serving_node'], 6)

    def test_hashrouting_symmetric_edge(self):
        hr = strategy.HashroutingClustered(self.view, self.controller,
                                           intra_routing='SYMM',
                                           inter_routing='EDGE')
        hr.authoritative_cache = lambda x, cluster: cluster * 3 + x
        # At time 1, receiver 0 requests content 2
        hr.process_event(1, "RCV", 3, True)
        loc = self.view.content_locations(3)
        self.assertEquals(2, len(loc))
        self.assertIn("SRC", loc)
        self.assertIn(3, loc)
        self.assertNotIn(6, loc)
        summary = self.collector.session_summary()
        exp_req_hops = [("RCV", 1), (1, 3), (3, 2), (2, 4), (4, 5), (5, "SRC")]
        exp_cont_hops = [("SRC", 5), (5, 4), (4, 2), (2, 3), (3, 1), (1, "RCV")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(set(exp_req_hops), set(req_hops))
        self.assertSetEqual(set(exp_cont_hops), set(cont_hops))
        self.assertEqual(summary['serving_node'], "SRC")
        # Expect hit from first cluster
        hr.process_event(1, "RCV", 3, True)
        loc = self.view.content_locations(3)
        self.assertEquals(len(loc), 2)
        self.assertIn("SRC", loc)
        self.assertIn(3, loc)
        self.assertNotIn(6, loc)
        summary = self.collector.session_summary()
        exp_req_hops = [("RCV", 1), (1, 3)]
        exp_cont_hops = [(3, 1), (1, "RCV")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(set(exp_req_hops), set(req_hops))
        self.assertSetEqual(set(exp_cont_hops), set(cont_hops))
        self.assertEqual(summary['serving_node'], 3)
        # Delete entry on first cluster, expect miss
        self.model.cache[3].remove(3)
        hr.process_event(1, "RCV", 3, True)
        loc = self.view.content_locations(3)
        self.assertEquals(len(loc), 2)
        self.assertIn("SRC", loc)
        self.assertIn(3, loc)
        self.assertNotIn(6, loc)
        summary = self.collector.session_summary()
        exp_req_hops = [("RCV", 1), (1, 3), (3, 2), (2, 4), (4, 5), (5, "SRC")]
        exp_cont_hops = [("SRC", 5), (5, 4), (4, 2), (2, 3), (3, 1), (1, "RCV")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(set(exp_req_hops), set(req_hops))
        self.assertSetEqual(set(exp_cont_hops), set(cont_hops))
        self.assertEqual("SRC", summary['serving_node'])

    def test_hashrouting_asymmetric_edge(self):
        hr = strategy.HashroutingClustered(self.view, self.controller,
                                           intra_routing='ASYMM',
                                           inter_routing='EDGE')
        hr.authoritative_cache = lambda x, cluster: cluster * 3 + x
        # Expect miss
        hr.process_event(1, "RCV", 3, True)
        loc = self.view.content_locations(3)
        self.assertEquals(len(loc), 1)
        self.assertIn("SRC", loc)
        self.assertNotIn(3, loc)
        self.assertNotIn(6, loc)
        summary = self.collector.session_summary()
        exp_req_hops = [("RCV", 1), (1, 3), (3, 2), (2, 4), (4, 5), (5, "SRC")]
        exp_cont_hops = [("SRC", 5), (5, 4), (4, 2), (2, 1), (1, "RCV")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(set(exp_req_hops), set(req_hops))
        self.assertSetEqual(set(exp_cont_hops), set(cont_hops))
        self.assertEqual(summary['serving_node'], "SRC")
        # Expect miss again, but this time caches will be populated
        hr.process_event(1, "RCV", 2, True)
        loc = self.view.content_locations(2)
        self.assertEquals(len(loc), 3)
        self.assertIn("SRC", loc)
        self.assertIn(2, loc)
        self.assertIn(5, loc)
        summary = self.collector.session_summary()
        exp_req_hops = [("RCV", 1), (1, 2), (2, 4), (4, 5), (5, 'SRC')]
        exp_cont_hops = [("SRC", 5), (5, 4), (4, 2), (2, 1), (1, "RCV")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(set(exp_req_hops), set(req_hops))
        self.assertSetEqual(set(exp_cont_hops), set(cont_hops))
        self.assertEqual(summary['serving_node'], "SRC")
        # Expect hit
        hr.process_event(1, "RCV", 2, True)
        loc = self.view.content_locations(2)
        self.assertEquals(len(loc), 3)
        self.assertIn("SRC", loc)
        self.assertIn(2, loc)
        self.assertIn(5, loc)
        summary = self.collector.session_summary()
        exp_req_hops = [("RCV", 1), (1, 2)]
        exp_cont_hops = [(2, 1), (1, "RCV")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(set(exp_req_hops), set(req_hops))
        self.assertSetEqual(set(exp_cont_hops), set(cont_hops))
        self.assertEqual(summary['serving_node'], 2)

    def test_hashrouting_multicast_edge(self):
        hr = strategy.HashroutingClustered(self.view, self.controller,
                                           intra_routing='MULTICAST',
                                           inter_routing='EDGE')
        hr.authoritative_cache = lambda x, cluster: cluster * 3 + x
        # At time 1, receiver 0 requests content 2
        hr.process_event(1, "RCV", 3, True)
        loc = self.view.content_locations(3)
        self.assertEquals(len(loc), 2)
        self.assertIn("SRC", loc)
        self.assertIn(3, loc)
        self.assertNotIn(6, loc)
        summary = self.collector.session_summary()
        exp_req_hops = [("RCV", 1), (1, 3), (3, 2), (2, 4), (4, 5), (5, "SRC")]
        exp_cont_hops = [("SRC", 5), (5, 4), (4, 2), (2, 3), (2, 1), (1, "RCV")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(set(exp_req_hops), set(req_hops))
        self.assertSetEqual(set(exp_cont_hops), set(cont_hops))
        self.assertEqual(summary['serving_node'], "SRC")
        # Expect hit from first cluster
        hr.process_event(1, "RCV", 3, True)
        loc = self.view.content_locations(3)
        self.assertEquals(len(loc), 2)
        self.assertIn("SRC", loc)
        self.assertIn(3, loc)
        self.assertNotIn(6, loc)
        summary = self.collector.session_summary()
        exp_req_hops = [("RCV", 1), (1, 3)]
        exp_cont_hops = [(3, 1), (1, "RCV")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(set(exp_req_hops), set(req_hops))
        self.assertSetEqual(set(exp_cont_hops), set(cont_hops))
        self.assertEqual(summary['serving_node'], 3)
        # Delete entry on first cluster, expect miss
        self.model.cache[3].remove(3)
        hr.process_event(1, "RCV", 3, True)
        loc = self.view.content_locations(3)
        self.assertEquals(2, len(loc))
        self.assertIn("SRC", loc)
        self.assertIn(3, loc)
        self.assertNotIn(6, loc)
        summary = self.collector.session_summary()
        exp_req_hops = [("RCV", 1), (1, 3), (3, 2), (2, 4), (4, 5), (5, "SRC")]
        exp_cont_hops = [("SRC", 5), (5, 4), (4, 2), (2, 3), (2, 1), (1, "RCV")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(set(exp_req_hops), set(req_hops))
        self.assertSetEqual(set(exp_cont_hops), set(cont_hops))
        self.assertEqual("SRC", summary['serving_node'])



class TestHashrouting(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    @classmethod
    def topology(cls):
        """Return topology for testing off-path caching strategies
        """
        # Topology sketch
        #
        #     -------- 5 ----------
        #    /                      \
        #   /                        \
        # 0 ---- 1 ---- 2 ---- 3 ---- 4
        #               |
        #               |
        #               6
        #
        topology = IcnTopology(fnss.ring_topology(6))
        topology.add_edge(2, 6)
        topology.add_edge(1, 7)
        source = 4
        receivers = (0, 6, 7)
        caches = (1, 2, 3, 5)
        contents = caches
        fnss.add_stack(topology, source, 'source', {'contents': contents})
        for v in caches:
            fnss.add_stack(topology, v, 'router', {'cache_size': 1})
        for v in receivers:
            fnss.add_stack(topology, v, 'receiver', {})
        return topology

    def setUp(self):
        topology = self.topology()
        model = NetworkModel(topology, cache_policy={'name': 'FIFO'})
        self.view = NetworkView(model)
        self.controller = NetworkController(model)
        self.collector = DummyCollector(self.view)
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

    def test_hashrouting_hybrid_am_max_stretch_0(self):
        hr = strategy.HashroutingHybridAM(self.view, self.controller, max_stretch=0)
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

    def test_hashrouting_hybrid_am_max_stretch_1(self):
        hr = strategy.HashroutingHybridAM(self.view, self.controller, max_stretch=1.0)
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

    @classmethod
    def on_path_topology(cls):
        """Return topology for testing on-path caching strategies
        """
        # Topology sketch
        #
        # 0 ---- 1 ---- 2 ---- 3 ---- 4
        #               |
        #               |
        #               5
        #
        topology = IcnTopology(fnss.line_topology(5))
        topology.add_edge(2, 5)
        source = 4
        receivers = (0, 5)
        caches = (1, 2, 3)
        contents = caches
        fnss.add_stack(topology, source, 'source', {'contents': contents})
        for v in caches:
            fnss.add_stack(topology, v, 'router', {'cache_size': 1})
        for v in receivers:
            fnss.add_stack(topology, v, 'receiver', {})
        return topology

    def setUp(self):
        topology = self.on_path_topology()
        model = NetworkModel(topology, cache_policy={'name': 'FIFO'})
        self.view = NetworkView(model)
        self.controller = NetworkController(model)
        self.collector = DummyCollector(self.view)
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
        exp_req_hops = [(0, 1), (1, 2), (2, 3), (3, 4)]
        exp_cont_hops = [(4, 3), (3, 2), (2, 1), (1, 0)]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(set(exp_req_hops), set(req_hops))
        self.assertSetEqual(set(exp_cont_hops), set(cont_hops))
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
        exp_req_hops = [(0, 1), (1, 2), (2, 3), (3, 4)]
        exp_cont_hops = [(4, 3), (3, 2), (2, 1), (1, 0)]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(set(exp_req_hops), set(req_hops))
        self.assertSetEqual(set(exp_cont_hops), set(cont_hops))
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
        exp_req_hops = [(5, 2), (2, 3), (3, 4)]
        exp_cont_hops = [(4, 3), (3, 2), (2, 5)]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(set(exp_req_hops), set(req_hops))
        self.assertSetEqual(set(exp_cont_hops), set(cont_hops))
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

    def test_edge(self):
        hr = strategy.Edge(self.view, self.controller)
        # receiver 0 requests 2, expect miss
        hr.process_event(1, 0, 2, True)
        loc = self.view.content_locations(2)
        self.assertEquals(len(loc), 2)
        self.assertIn(1, loc)
        self.assertNotIn(2, loc)
        self.assertNotIn(3, loc)
        self.assertIn(4, loc)
        summary = self.collector.session_summary()
        exp_req_hops = [(0, 1), (1, 2), (2, 3), (3, 4)]
        exp_cont_hops = [(4, 3), (3, 2), (2, 1), (1, 0)]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(set(exp_req_hops), set(req_hops))
        self.assertSetEqual(set(exp_cont_hops), set(cont_hops))
        self.assertEqual(4, summary['serving_node'])
        # receiver 0 requests 2, expect hit
        hr.process_event(1, 0, 2, True)
        loc = self.view.content_locations(2)
        self.assertEquals(len(loc), 2)
        self.assertIn(1, loc)
        self.assertNotIn(2, loc)
        self.assertNotIn(3, loc)
        self.assertIn(4, loc)
        summary = self.collector.session_summary()
        exp_req_hops = [(0, 1)]
        exp_cont_hops = [(1, 0)]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(set(exp_req_hops), set(req_hops))
        self.assertSetEqual(set(exp_cont_hops), set(cont_hops))
        self.assertEqual(1, summary['serving_node'])
        hr.process_event(1, 5, 2, True)
        loc = self.view.content_locations(2)
        self.assertEquals(len(loc), 3)
        self.assertIn(1, loc)
        self.assertIn(2, loc)
        self.assertNotIn(3, loc)
        self.assertIn(4, loc)
        summary = self.collector.session_summary()
        exp_req_hops = [(5, 2), (2, 3), (3, 4)]
        exp_cont_hops = [(4, 3), (3, 2), (2, 5)]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(set(exp_req_hops), set(req_hops))
        self.assertSetEqual(set(exp_cont_hops), set(cont_hops))
        self.assertEqual(4, summary['serving_node'])
        hr.process_event(1, 5, 2, True)
        loc = self.view.content_locations(2)
        self.assertEquals(len(loc), 3)
        self.assertIn(1, loc)
        self.assertIn(2, loc)
        self.assertNotIn(3, loc)
        self.assertIn(4, loc)
        summary = self.collector.session_summary()
        exp_req_hops = [(5, 2)]
        exp_cont_hops = [(2, 5)]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(set(exp_req_hops), set(req_hops))
        self.assertSetEqual(set(exp_cont_hops), set(cont_hops))
        self.assertEqual(2, summary['serving_node'])

    def test_lcd(self):
        hr = strategy.LeaveCopyDown(self.view, self.controller)
        # receiver 0 requests 2, expect miss
        hr.process_event(1, 0, 2, True)
        loc = self.view.content_locations(2)
        self.assertEquals(len(loc), 2)
        self.assertIn(3, loc)
        self.assertIn(4, loc)
        summary = self.collector.session_summary()
        exp_req_hops = [(0, 1), (1, 2), (2, 3), (3, 4)]
        exp_cont_hops = [(4, 3), (3, 2), (2, 1), (1, 0)]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(set(exp_req_hops), set(req_hops))
        self.assertSetEqual(set(exp_cont_hops), set(cont_hops))
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
        exp_req_hops = [(0, 1), (1, 2)]
        exp_cont_hops = [(2, 1), (1, 0)]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(set(exp_req_hops), set(req_hops))
        self.assertSetEqual(set(exp_cont_hops), set(cont_hops))
        # receiver 0 requests 2, expect hit in 1
        hr.process_event(1, 0, 2, True)
        loc = self.view.content_locations(2)
        self.assertEquals(len(loc), 4)
        self.assertIn(1, loc)
        self.assertIn(2, loc)
        self.assertIn(3, loc)
        self.assertIn(4, loc)
        summary = self.collector.session_summary()
        exp_req_hops = [(0, 1)]
        exp_cont_hops = [(1, 0)]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(set(exp_req_hops), set(req_hops))
        self.assertSetEqual(set(exp_cont_hops), set(cont_hops))
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
        exp_req_hops = [(0, 1), (1, 2), (2, 3), (3, 4)]
        exp_cont_hops = [(4, 3), (3, 2), (2, 1), (1, 0)]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(set(exp_req_hops), set(req_hops))
        self.assertSetEqual(set(exp_cont_hops), set(cont_hops))

    def test_cl4m(self):
        hr = strategy.CacheLessForMore(self.view, self.controller)
        # receiver 0 requests 2, expect miss
        hr.process_event(1, 0, 2, True)
        loc = self.view.content_locations(2)
        self.assertEquals(len(loc), 2)
        self.assertIn(2, loc)
        self.assertIn(4, loc)
        summary = self.collector.session_summary()
        exp_req_hops = [(0, 1), (1, 2), (2, 3), (3, 4)]
        exp_cont_hops = [(4, 3), (3, 2), (2, 1), (1, 0)]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(set(exp_req_hops), set(req_hops))
        self.assertSetEqual(set(exp_cont_hops), set(cont_hops))
        # receiver 0 requests 2, expect hit
        hr.process_event(1, 0, 2, True)
        loc = self.view.content_locations(2)
        self.assertEquals(len(loc), 3)
        self.assertIn(1, loc)
        self.assertIn(2, loc)
        self.assertIn(4, loc)
        summary = self.collector.session_summary()
        exp_req_hops = [(0, 1), (1, 2)]
        exp_cont_hops = [(2, 1), (1, 0)]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(set(exp_req_hops), set(req_hops))
        self.assertSetEqual(set(exp_cont_hops), set(cont_hops))
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
        exp_req_hops = [(0, 1), (1, 2), (2, 3), (3, 4)]
        exp_cont_hops = [(4, 3), (3, 2), (2, 1), (1, 0)]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        self.assertSetEqual(set(exp_req_hops), set(req_hops))
        self.assertSetEqual(set(exp_cont_hops), set(cont_hops))

    def test_random_choice(self):
        hr = strategy.RandomChoice(self.view, self.controller)
        hr.process_event(1, 0, 2, True)
        loc = self.view.content_locations(2)
        self.assertEquals(len(loc), 2)
        self.assertIn(4, loc)
        summary = self.collector.session_summary()
        self.assertEqual(4, summary['serving_node'])

    def test_random_bernoulli(self):
        hr = strategy.RandomBernoulli(self.view, self.controller)
        hr.process_event(1, 0, 2, True)
        loc = self.view.content_locations(2)
        self.assertIn(4, loc)
        summary = self.collector.session_summary()
        self.assertEqual(4, summary['serving_node'])

    def test_random_bernoulli_p_0(self):
        hr = strategy.RandomBernoulli(self.view, self.controller, p=0)
        hr.process_event(1, 0, 2, True)
        loc = self.view.content_locations(2)
        self.assertNotIn(1, loc)
        self.assertNotIn(2, loc)
        self.assertNotIn(3, loc)
        self.assertIn(4, loc)
        summary = self.collector.session_summary()
        self.assertEqual(4, summary['serving_node'])
        hr.process_event(1, 0, 2, True)
        loc = self.view.content_locations(2)
        self.assertNotIn(1, loc)
        self.assertNotIn(2, loc)
        self.assertNotIn(3, loc)
        self.assertIn(4, loc)
        summary = self.collector.session_summary()
        self.assertEqual(4, summary['serving_node'])

    def test_random_bernoulli_p_1(self):
        hr = strategy.RandomBernoulli(self.view, self.controller, p=1)
        hr.process_event(1, 0, 2, True)
        loc = self.view.content_locations(2)
        self.assertIn(1, loc)
        self.assertIn(2, loc)
        self.assertIn(3, loc)
        self.assertIn(4, loc)
        summary = self.collector.session_summary()
        self.assertEqual(4, summary['serving_node'])
        hr.process_event(1, 0, 2, True)
        loc = self.view.content_locations(2)
        self.assertIn(1, loc)
        self.assertIn(2, loc)
        self.assertIn(3, loc)
        self.assertIn(4, loc)
        summary = self.collector.session_summary()
        self.assertEqual(1, summary['serving_node'])


class TestPartition(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    @classmethod
    def partition_topology(cls):
        #
        #      +-- s1 --+
        #     /     |    \
        #   c1-----[]----c2
        #         /  \
        #        r1  r2
        #
        topo = fnss.Topology()
        icr_candidates = ["c1", "router", "c2"]
        topo.add_path(icr_candidates)
        topo.add_edge("r1", "router")
        topo.add_edge("r2", "router")
        topo.add_edge("c1", "s1")
        topo.add_edge("c2", "s1")
        topo.graph['icr_candidates'] = set(icr_candidates)
        contents = (1, 2, 3, 4)
        for router in icr_candidates:
            if router in ("c1", "c2"):
                props = {'cache_size': 1}
            fnss.add_stack(topo, router, 'router', **props)
        for src in ['s1']:
            fnss.add_stack(topo, src, 'source', {'contents': contents})
        for rcv in ['r1', 'r2']:
            fnss.add_stack(topo, rcv, 'receiver')
        topo.graph['cache_assignment'] = {"r1": "c1", "r2": "c2"}
        return IcnTopology(topo)

    def setUp(self):
        topology = self.partition_topology()
        model = NetworkModel(topology, cache_policy={'name': 'FIFO'})
        self.view = NetworkView(model)
        self.controller = NetworkController(model)
        self.collector = DummyCollector(self.view)
        self.controller.attach_collector(self.collector)

    def tearDown(self):
        pass

    def test(self):
        hr = strategy.Partition(self.view, self.controller)
        # receiver 0 requests 2, expect miss
        hr.process_event(1, "r1", 2, True)
        loc = self.view.content_locations(2)
        self.assertEquals(2, len(loc))
        self.assertIn("s1", loc)
        self.assertIn("c1", loc)
        self.assertNotIn("c2", loc)
        summary = self.collector.session_summary()
        exp_req_hops = [("r1", "router"), ("router", "c1"), ("c1", "s1")]
        exp_cont_hops = [("s1", "c1"), ("c1", "router"), ("router", "r1")]
        self.assertSetEqual(set(exp_req_hops), set(summary['request_hops']))
        self.assertSetEqual(set(exp_cont_hops), set(summary['content_hops']))
        self.assertEqual("s1", summary['serving_node'])
        # receiver 0 requests 2, expect hit
        hr.process_event(1, "r1", 2, True)
        loc = self.view.content_locations(2)
        self.assertEquals(2, len(loc))
        self.assertIn("s1", loc)
        self.assertIn("c1", loc)
        self.assertNotIn("c2", loc)
        summary = self.collector.session_summary()
        exp_req_hops = [("r1", "router"), ("router", "c1")]
        exp_cont_hops = [("c1", "router"), ("router", "r1")]
        self.assertSetEqual(set(exp_req_hops), set(summary['request_hops']))
        self.assertSetEqual(set(exp_cont_hops), set(summary['content_hops']))
        self.assertEqual("c1", summary['serving_node'])
        # Now try with other partition
        hr.process_event(1, "r2", 2, True)
        loc = self.view.content_locations(2)
        self.assertEquals(3, len(loc))
        self.assertIn("s1", loc)
        self.assertIn("c1", loc)
        self.assertIn("c2", loc)
        summary = self.collector.session_summary()
        exp_req_hops = [("r2", "router"), ("router", "c2"), ("c2", "s1")]
        exp_cont_hops = [("s1", "c2"), ("c2", "router"), ("router", "r2")]
        self.assertSetEqual(set(exp_req_hops), set(summary['request_hops']))
        self.assertSetEqual(set(exp_cont_hops), set(summary['content_hops']))
        self.assertEqual("s1", summary['serving_node'])
        hr.process_event(1, "r2", 2, True)
        loc = self.view.content_locations(2)
        self.assertEquals(3, len(loc))
        self.assertIn("s1", loc)
        self.assertIn("c1", loc)
        self.assertIn("c2", loc)
        summary = self.collector.session_summary()
        exp_req_hops = [("r2", "router"), ("router", "c2")]
        exp_cont_hops = [("c2", "router"), ("router", "r2")]
        self.assertSetEqual(set(exp_req_hops), set(summary['request_hops']))
        self.assertSetEqual(set(exp_cont_hops), set(summary['content_hops']))
        self.assertEqual("c2", summary['serving_node'])


class TestNrr(unittest.TestCase):
    """Test suite for Nearest Replica Routing strategies
    """

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    @classmethod
    def nrr_topology(cls):
        """Return topology for testing NRR caching strategies
        """
        # Topology sketch
        #
        # 0 ---- 2----- 4
        #        |       \
        #        |        s
        #        |       /
        # 1 ---- 3 ---- 5
        #
        topology = IcnTopology(fnss.Topology())
        topology.add_path([0, 2, 4, "s", 5, 3, 1])
        topology.add_edge(2, 3)
        receivers = (0, 1)
        source = "s"
        caches = (2, 3, 4, 5)
        contents = (1, 2, 3, 4)
        fnss.add_stack(topology, source, 'source', {'contents': contents})
        for v in caches:
            fnss.add_stack(topology, v, 'router', {'cache_size': 1})
        for v in receivers:
            fnss.add_stack(topology, v, 'receiver', {})
        fnss.set_delays_constant(topology, 1, 'ms')
        return topology

    def setUp(self):
        topology = self.nrr_topology()
        model = NetworkModel(topology, cache_policy={'name': 'FIFO'})
        self.view = NetworkView(model)
        self.controller = NetworkController(model)
        self.collector = DummyCollector(self.view)
        self.controller.attach_collector(self.collector)

    def tearDown(self):
        pass

    def test_lce(self):
        hr = strategy.NearestReplicaRouting(self.view, self.controller, metacaching='LCE')
        # receiver 0 requests 2, expect miss
        hr.process_event(1, 0, 2, True)
        loc = self.view.content_locations(2)
        self.assertEquals(3, len(loc))
        self.assertIn(2, loc)
        self.assertIn(4, loc)
        self.assertIn("s", loc)
        self.assertNotIn(3, loc)
        self.assertNotIn(5, loc)
        summary = self.collector.session_summary()
        exp_req_hops = [(0, 2), (2, 4), (4, "s")]
        exp_cont_hops = [("s", 4), (4, 2), (2, 0)]
        self.assertSetEqual(set(exp_req_hops), set(summary['request_hops']))
        self.assertSetEqual(set(exp_cont_hops), set(summary['content_hops']))
        self.assertEqual("s", summary['serving_node'])
        hr.process_event(1, 1, 2, True)
        loc = self.view.content_locations(2)
        self.assertEquals(4, len(loc))
        self.assertIn(2, loc)
        self.assertIn(4, loc)
        self.assertIn("s", loc)
        self.assertIn(3, loc)
        self.assertNotIn(5, loc)
        summary = self.collector.session_summary()
        exp_req_hops = [(1, 3), (3, 2)]
        exp_cont_hops = [(2, 3), (3, 1)]
        self.assertSetEqual(set(exp_req_hops), set(summary['request_hops']))
        self.assertSetEqual(set(exp_cont_hops), set(summary['content_hops']))
        self.assertEqual(2, summary['serving_node'])
        hr.process_event(1, 1, 2, True)
        loc = self.view.content_locations(2)
        self.assertEquals(4, len(loc))
        self.assertIn(2, loc)
        self.assertIn(4, loc)
        self.assertIn("s", loc)
        self.assertIn(3, loc)
        self.assertNotIn(5, loc)
        summary = self.collector.session_summary()
        exp_req_hops = [(1, 3)]
        exp_cont_hops = [(3, 1)]
        self.assertSetEqual(set(exp_req_hops), set(summary['request_hops']))
        self.assertSetEqual(set(exp_cont_hops), set(summary['content_hops']))
        self.assertEqual(3, summary['serving_node'])


    def test_lcd(self):
        hr = strategy.NearestReplicaRouting(self.view, self.controller, metacaching='LCD')
        # receiver 0 requests 2, expect miss
        hr.process_event(1, 0, 2, True)
        loc = self.view.content_locations(2)
        self.assertEquals(2, len(loc))
        self.assertNotIn(2, loc)
        self.assertIn(4, loc)
        self.assertIn("s", loc)
        self.assertNotIn(3, loc)
        self.assertNotIn(5, loc)
        summary = self.collector.session_summary()
        exp_req_hops = [(0, 2), (2, 4), (4, "s")]
        exp_cont_hops = [("s", 4), (4, 2), (2, 0)]
        self.assertSetEqual(set(exp_req_hops), set(summary['request_hops']))
        self.assertSetEqual(set(exp_cont_hops), set(summary['content_hops']))
        self.assertEqual("s", summary['serving_node'])
        hr.process_event(1, 0, 2, True)
        loc = self.view.content_locations(2)
        self.assertEquals(3, len(loc))
        self.assertIn(2, loc)
        self.assertIn(4, loc)
        self.assertIn("s", loc)
        self.assertNotIn(3, loc)
        self.assertNotIn(5, loc)
        summary = self.collector.session_summary()
        exp_req_hops = [(0, 2), (2, 4)]
        exp_cont_hops = [(4, 2), (2, 0)]
        self.assertSetEqual(set(exp_req_hops), set(summary['request_hops']))
        self.assertSetEqual(set(exp_cont_hops), set(summary['content_hops']))
        self.assertEqual(4, summary['serving_node'])
        hr.process_event(1, 1, 2, True)
        loc = self.view.content_locations(2)
        self.assertEquals(4, len(loc))
        self.assertIn(2, loc)
        self.assertIn(4, loc)
        self.assertIn("s", loc)
        self.assertIn(3, loc)
        self.assertNotIn(5, loc)
        summary = self.collector.session_summary()
        exp_req_hops = [(1, 3), (3, 2)]
        exp_cont_hops = [(2, 3), (3, 1)]
        self.assertSetEqual(set(exp_req_hops), set(summary['request_hops']))
        self.assertSetEqual(set(exp_cont_hops), set(summary['content_hops']))
        self.assertEqual(2, summary['serving_node'])
        hr.process_event(1, 1, 2, True)
        loc = self.view.content_locations(2)
        self.assertEquals(4, len(loc))
        self.assertIn(2, loc)
        self.assertIn(4, loc)
        self.assertIn("s", loc)
        self.assertIn(3, loc)
        self.assertNotIn(5, loc)
        summary = self.collector.session_summary()
        exp_req_hops = [(1, 3)]
        exp_cont_hops = [(3, 1)]
        self.assertSetEqual(set(exp_req_hops), set(summary['request_hops']))
        self.assertSetEqual(set(exp_cont_hops), set(summary['content_hops']))
        self.assertEqual(3, summary['serving_node'])
