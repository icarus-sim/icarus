import unittest

import networkx as nx
import fnss

from icarus.scenarios import IcnTopology
import icarus.models as strategy
from icarus.execution import NetworkModel, NetworkView, NetworkController, DummyCollector


class TestOnPath(unittest.TestCase):

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

    def test_lce_same_content(self):
        hr = strategy.LeaveCopyEverywhere(self.view, self.controller)
        # receiver 0 requests 2, expect miss
        hr.process_event(1, 0, 2, True)
        loc = self.view.content_locations(2)
        self.assertEqual(len(loc), 4)
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
        self.assertEqual(len(loc), 4)
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
        self.assertEqual(len(loc), 4)
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
        self.assertEqual(len(loc), 3)
        self.assertIn(2, loc)
        self.assertIn(3, loc)
        self.assertIn(4, loc)
        loc = self.view.content_locations(2)
        self.assertEqual(len(loc), 2)
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
        self.assertEqual(len(loc), 4)
        self.assertIn(1, loc)
        self.assertIn(2, loc)
        self.assertIn(3, loc)
        self.assertIn(4, loc)
        loc = self.view.content_locations(2)
        self.assertEqual(len(loc), 1)
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
        self.assertEqual(len(loc), 2)
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
        self.assertEqual(len(loc), 2)
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
        self.assertEqual(len(loc), 3)
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
        self.assertEqual(len(loc), 3)
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
        self.assertEqual(len(loc), 2)
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
        self.assertEqual(len(loc), 3)
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
        self.assertEqual(len(loc), 4)
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
        self.assertEqual(len(loc), 4)
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
        self.assertEqual(len(loc), 3)
        self.assertIn(1, loc)
        self.assertIn(2, loc)
        self.assertIn(4, loc)
        loc = self.view.content_locations(3)
        self.assertEqual(len(loc), 2)
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
        self.assertEqual(len(loc), 2)
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
        self.assertEqual(len(loc), 3)
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
        self.assertEqual(len(loc), 2)
        self.assertIn(1, loc)
        self.assertIn(4, loc)
        loc = self.view.content_locations(3)
        self.assertEqual(len(loc), 2)
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
        self.assertEqual(len(loc), 2)
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
        nx.add_path(topo, icr_candidates)
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

    def test(self):
        hr = strategy.Partition(self.view, self.controller)
        # receiver 0 requests 2, expect miss
        hr.process_event(1, "r1", 2, True)
        loc = self.view.content_locations(2)
        self.assertEqual(2, len(loc))
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
        self.assertEqual(2, len(loc))
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
        self.assertEqual(3, len(loc))
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
        self.assertEqual(3, len(loc))
        self.assertIn("s1", loc)
        self.assertIn("c1", loc)
        self.assertIn("c2", loc)
        summary = self.collector.session_summary()
        exp_req_hops = [("r2", "router"), ("router", "c2")]
        exp_cont_hops = [("c2", "router"), ("router", "r2")]
        self.assertSetEqual(set(exp_req_hops), set(summary['request_hops']))
        self.assertSetEqual(set(exp_cont_hops), set(summary['content_hops']))
        self.assertEqual("c2", summary['serving_node'])
