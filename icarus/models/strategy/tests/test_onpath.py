import networkx as nx
import fnss

from icarus.scenarios import IcnTopology
import icarus.models as strategy
from icarus.execution import NetworkModel, NetworkView, NetworkController, DummyCollector


class TestOnPath(object):

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

    def setup_method(self):
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
        assert len(loc) == 4
        assert 1 in loc
        assert 2 in loc
        assert 3 in loc
        assert 4 in loc
        summary = self.collector.session_summary()
        exp_req_hops = [(0, 1), (1, 2), (2, 3), (3, 4)]
        exp_cont_hops = [(4, 3), (3, 2), (2, 1), (1, 0)]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert set(exp_req_hops) == set(req_hops)
        assert set(exp_cont_hops) == set(cont_hops)
        # receiver 0 requests 2, expect hit
        hr.process_event(1, 5, 2, True)
        loc = self.view.content_locations(2)
        assert len(loc) == 4
        assert 1 in loc
        assert 2 in loc
        assert 3 in loc
        assert 4 in loc
        summary = self.collector.session_summary()
        exp_req_hops = set(((5, 2),))
        exp_cont_hops = set(((2, 5),))
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert exp_req_hops == set(req_hops)
        assert exp_cont_hops == set(cont_hops)

    def test_lce_different_content(self):
        hr = strategy.LeaveCopyEverywhere(self.view, self.controller)
        # receiver 0 requests 2, expect miss
        hr.process_event(1, 0, 2, True)
        loc = self.view.content_locations(2)
        assert len(loc) == 4
        assert 1 in loc
        assert 2 in loc
        assert 3 in loc
        assert 4 in loc
        summary = self.collector.session_summary()
        exp_req_hops = [(0, 1), (1, 2), (2, 3), (3, 4)]
        exp_cont_hops = [(4, 3), (3, 2), (2, 1), (1, 0)]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert set(exp_req_hops) == set(req_hops)
        assert set(exp_cont_hops) == set(cont_hops)
        # request content 3 from 5
        hr.process_event(1, 5, 3, True)
        loc = self.view.content_locations(3)
        assert len(loc) == 3
        assert 2 in loc
        assert 3 in loc
        assert 4 in loc
        loc = self.view.content_locations(2)
        assert len(loc) == 2
        assert 1 in loc
        assert 4 in loc
        summary = self.collector.session_summary()
        exp_req_hops = [(5, 2), (2, 3), (3, 4)]
        exp_cont_hops = [(4, 3), (3, 2), (2, 5)]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert set(exp_req_hops) == set(req_hops)
        assert set(exp_cont_hops) == set(cont_hops)
        # request content 3 from , hit in 2
        hr.process_event(1, 0, 3, True)
        loc = self.view.content_locations(3)
        assert len(loc) == 4
        assert 1 in loc
        assert 2 in loc
        assert 3 in loc
        assert 4 in loc
        loc = self.view.content_locations(2)
        assert len(loc) == 1
        assert 4 in loc
        summary = self.collector.session_summary()
        exp_req_hops = set(((0, 1), (1, 2)))
        exp_cont_hops = set(((2, 1), (1, 0)))
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert exp_req_hops == set(req_hops)
        assert exp_cont_hops == set(cont_hops)

    def test_edge(self):
        hr = strategy.Edge(self.view, self.controller)
        # receiver 0 requests 2, expect miss
        hr.process_event(1, 0, 2, True)
        loc = self.view.content_locations(2)
        assert len(loc) == 2
        assert 1 in loc
        assert 2 not in loc
        assert 3 not in loc
        assert 4 in loc
        summary = self.collector.session_summary()
        exp_req_hops = [(0, 1), (1, 2), (2, 3), (3, 4)]
        exp_cont_hops = [(4, 3), (3, 2), (2, 1), (1, 0)]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert set(exp_req_hops) == set(req_hops)
        assert set(exp_cont_hops) == set(cont_hops)
        assert 4 == summary['serving_node']
        # receiver 0 requests 2, expect hit
        hr.process_event(1, 0, 2, True)
        loc = self.view.content_locations(2)
        assert len(loc) == 2
        assert 1 in loc
        assert 2 not in loc
        assert 3 not in loc
        assert 4 in loc
        summary = self.collector.session_summary()
        exp_req_hops = [(0, 1)]
        exp_cont_hops = [(1, 0)]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert set(exp_req_hops) == set(req_hops)
        assert set(exp_cont_hops) == set(cont_hops)
        assert 1 == summary['serving_node']
        hr.process_event(1, 5, 2, True)
        loc = self.view.content_locations(2)
        assert len(loc) == 3
        assert 1 in loc
        assert 2 in loc
        assert 3 not in loc
        assert 4 in loc
        summary = self.collector.session_summary()
        exp_req_hops = [(5, 2), (2, 3), (3, 4)]
        exp_cont_hops = [(4, 3), (3, 2), (2, 5)]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert set(exp_req_hops) == set(req_hops)
        assert set(exp_cont_hops) == set(cont_hops)
        assert 4 == summary['serving_node']
        hr.process_event(1, 5, 2, True)
        loc = self.view.content_locations(2)
        assert len(loc) == 3
        assert 1 in loc
        assert 2 in loc
        assert 3 not in loc
        assert 4 in loc
        summary = self.collector.session_summary()
        exp_req_hops = [(5, 2)]
        exp_cont_hops = [(2, 5)]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert set(exp_req_hops) == set(req_hops)
        assert set(exp_cont_hops) == set(cont_hops)
        assert 2 == summary['serving_node']

    def test_lcd(self):
        hr = strategy.LeaveCopyDown(self.view, self.controller)
        # receiver 0 requests 2, expect miss
        hr.process_event(1, 0, 2, True)
        loc = self.view.content_locations(2)
        assert len(loc) == 2
        assert 3 in loc
        assert 4 in loc
        summary = self.collector.session_summary()
        exp_req_hops = [(0, 1), (1, 2), (2, 3), (3, 4)]
        exp_cont_hops = [(4, 3), (3, 2), (2, 1), (1, 0)]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert set(exp_req_hops) == set(req_hops)
        assert set(exp_cont_hops) == set(cont_hops)
        # receiver 0 requests 2, expect hit in 3
        hr.process_event(1, 0, 2, True)
        loc = self.view.content_locations(2)
        assert len(loc) == 3
        assert 2 in loc
        assert 3 in loc
        assert 4 in loc
        summary = self.collector.session_summary()
        exp_req_hops = set(((0, 1), (1, 2), (2, 3)))
        exp_cont_hops = set(((3, 2), (2, 1), (1, 0)))
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert exp_req_hops == set(req_hops)
        assert exp_cont_hops == set(cont_hops)
        # receiver 0 requests 2, expect hit in 2
        hr.process_event(1, 0, 2, True)
        loc = self.view.content_locations(2)
        assert len(loc) == 4
        assert 1 in loc
        assert 2 in loc
        assert 3 in loc
        assert 4 in loc
        summary = self.collector.session_summary()
        exp_req_hops = [(0, 1), (1, 2)]
        exp_cont_hops = [(2, 1), (1, 0)]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert set(exp_req_hops) == set(req_hops)
        assert set(exp_cont_hops) == set(cont_hops)
        # receiver 0 requests 2, expect hit in 1
        hr.process_event(1, 0, 2, True)
        loc = self.view.content_locations(2)
        assert len(loc) == 4
        assert 1 in loc
        assert 2 in loc
        assert 3 in loc
        assert 4 in loc
        summary = self.collector.session_summary()
        exp_req_hops = [(0, 1)]
        exp_cont_hops = [(1, 0)]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert set(exp_req_hops) == set(req_hops)
        assert set(exp_cont_hops) == set(cont_hops)
        # receiver 0 requests 3, expect miss and eviction of 2 from 3
        hr.process_event(1, 0, 3, True)
        loc = self.view.content_locations(2)
        assert len(loc) == 3
        assert 1 in loc
        assert 2 in loc
        assert 4 in loc
        loc = self.view.content_locations(3)
        assert len(loc) == 2
        assert 3 in loc
        assert 4 in loc
        summary = self.collector.session_summary()
        exp_req_hops = [(0, 1), (1, 2), (2, 3), (3, 4)]
        exp_cont_hops = [(4, 3), (3, 2), (2, 1), (1, 0)]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert set(exp_req_hops) == set(req_hops)
        assert set(exp_cont_hops) == set(cont_hops)

    def test_cl4m(self):
        hr = strategy.CacheLessForMore(self.view, self.controller)
        # receiver 0 requests 2, expect miss
        hr.process_event(1, 0, 2, True)
        loc = self.view.content_locations(2)
        assert len(loc) == 2
        assert 2 in loc
        assert 4 in loc
        summary = self.collector.session_summary()
        exp_req_hops = [(0, 1), (1, 2), (2, 3), (3, 4)]
        exp_cont_hops = [(4, 3), (3, 2), (2, 1), (1, 0)]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert set(exp_req_hops) == set(req_hops)
        assert set(exp_cont_hops) == set(cont_hops)
        # receiver 0 requests 2, expect hit
        hr.process_event(1, 0, 2, True)
        loc = self.view.content_locations(2)
        assert len(loc) == 3
        assert 1 in loc
        assert 2 in loc
        assert 4 in loc
        summary = self.collector.session_summary()
        exp_req_hops = [(0, 1), (1, 2)]
        exp_cont_hops = [(2, 1), (1, 0)]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert set(exp_req_hops) == set(req_hops)
        assert set(exp_cont_hops) == set(cont_hops)
        # receiver 0 requests 3, expect miss
        hr.process_event(1, 0, 3, True)
        loc = self.view.content_locations(2)
        assert len(loc) == 2
        assert 1 in loc
        assert 4 in loc
        loc = self.view.content_locations(3)
        assert len(loc) == 2
        assert 2 in loc
        assert 4 in loc
        summary = self.collector.session_summary()
        exp_req_hops = [(0, 1), (1, 2), (2, 3), (3, 4)]
        exp_cont_hops = [(4, 3), (3, 2), (2, 1), (1, 0)]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert set(exp_req_hops) == set(req_hops)
        assert set(exp_cont_hops) == set(cont_hops)

    def test_random_choice(self):
        hr = strategy.RandomChoice(self.view, self.controller)
        hr.process_event(1, 0, 2, True)
        loc = self.view.content_locations(2)
        assert len(loc) == 2
        assert 4 in loc
        summary = self.collector.session_summary()
        assert 4 == summary['serving_node']

    def test_random_bernoulli(self):
        hr = strategy.RandomBernoulli(self.view, self.controller)
        hr.process_event(1, 0, 2, True)
        loc = self.view.content_locations(2)
        assert 4 in loc
        summary = self.collector.session_summary()
        assert 4 == summary['serving_node']

    def test_random_bernoulli_p_0(self):
        hr = strategy.RandomBernoulli(self.view, self.controller, p=0)
        hr.process_event(1, 0, 2, True)
        loc = self.view.content_locations(2)
        assert 1 not in loc
        assert 2 not in loc
        assert 3 not in loc
        assert 4 in loc
        summary = self.collector.session_summary()
        assert 4 == summary['serving_node']
        hr.process_event(1, 0, 2, True)
        loc = self.view.content_locations(2)
        assert 1 not in loc
        assert 2 not in loc
        assert 3 not in loc
        assert 4 in loc
        summary = self.collector.session_summary()
        assert 4 == summary['serving_node']

    def test_random_bernoulli_p_1(self):
        hr = strategy.RandomBernoulli(self.view, self.controller, p=1)
        hr.process_event(1, 0, 2, True)
        loc = self.view.content_locations(2)
        assert 1 in loc
        assert 2 in loc
        assert 3 in loc
        assert 4 in loc
        summary = self.collector.session_summary()
        assert 4 == summary['serving_node']
        hr.process_event(1, 0, 2, True)
        loc = self.view.content_locations(2)
        assert 1 in loc
        assert 2 in loc
        assert 3 in loc
        assert 4 in loc
        summary = self.collector.session_summary()
        assert 1 == summary['serving_node']


class TestPartition(object):

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

    def setup_method(self):
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
        assert 2 == len(loc)
        assert "s1" in loc
        assert "c1" in loc
        assert "c2" not in loc
        summary = self.collector.session_summary()
        exp_req_hops = [("r1", "router"), ("router", "c1"), ("c1", "s1")]
        exp_cont_hops = [("s1", "c1"), ("c1", "router"), ("router", "r1")]
        assert set(exp_req_hops) == set(summary['request_hops'])
        assert set(exp_cont_hops) == set(summary['content_hops'])
        assert "s1" == summary['serving_node']
        # receiver 0 requests 2, expect hit
        hr.process_event(1, "r1", 2, True)
        loc = self.view.content_locations(2)
        assert 2 == len(loc)
        assert "s1" in loc
        assert "c1" in loc
        assert "c2" not in loc
        summary = self.collector.session_summary()
        exp_req_hops = [("r1", "router"), ("router", "c1")]
        exp_cont_hops = [("c1", "router"), ("router", "r1")]
        assert set(exp_req_hops) == set(summary['request_hops'])
        assert set(exp_cont_hops) == set(summary['content_hops'])
        assert "c1" == summary['serving_node']
        # Now try with other partition
        hr.process_event(1, "r2", 2, True)
        loc = self.view.content_locations(2)
        assert 3 == len(loc)
        assert "s1" in loc
        assert "c1" in loc
        assert "c2" in loc
        summary = self.collector.session_summary()
        exp_req_hops = [("r2", "router"), ("router", "c2"), ("c2", "s1")]
        exp_cont_hops = [("s1", "c2"), ("c2", "router"), ("router", "r2")]
        assert set(exp_req_hops) == set(summary['request_hops'])
        assert set(exp_cont_hops) == set(summary['content_hops'])
        assert "s1" == summary['serving_node']
        hr.process_event(1, "r2", 2, True)
        loc = self.view.content_locations(2)
        assert 3 == len(loc)
        assert "s1" in loc
        assert "c1" in loc
        assert "c2" in loc
        summary = self.collector.session_summary()
        exp_req_hops = [("r2", "router"), ("router", "c2")]
        exp_cont_hops = [("c2", "router"), ("router", "r2")]
        assert set(exp_req_hops) == set(summary['request_hops'])
        assert set(exp_cont_hops) == set(summary['content_hops'])
        assert "c2" == summary['serving_node']
