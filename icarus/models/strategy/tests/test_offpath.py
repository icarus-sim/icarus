import networkx as nx
import fnss

from icarus.scenarios import IcnTopology
import icarus.models as strategy
from icarus.execution import NetworkModel, NetworkView, NetworkController, DummyCollector


class TestNrr(object):
    """Test suite for Nearest Replica Routing strategies"""

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
        nx.add_path(topology, [0, 2, 4, "s", 5, 3, 1])
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

    def setup_method(self):
        topology = self.nrr_topology()
        model = NetworkModel(topology, cache_policy={'name': 'FIFO'})
        self.view = NetworkView(model)
        self.controller = NetworkController(model)
        self.collector = DummyCollector(self.view)
        self.controller.attach_collector(self.collector)

    def test_lce(self):
        hr = strategy.NearestReplicaRouting(self.view, self.controller, metacaching='LCE')
        # receiver 0 requests 2, expect miss
        hr.process_event(1, 0, 2, True)
        loc = self.view.content_locations(2)
        assert 3 == len(loc)
        assert 2 in loc
        assert 4 in loc
        assert "s" in loc
        assert 3 not in loc
        assert 5 not in loc
        summary = self.collector.session_summary()
        exp_req_hops = [(0, 2), (2, 4), (4, "s")]
        exp_cont_hops = [("s", 4), (4, 2), (2, 0)]
        assert set(exp_req_hops) == set(summary['request_hops'])
        assert set(exp_cont_hops) == set(summary['content_hops'])
        assert "s" == summary['serving_node']
        hr.process_event(1, 1, 2, True)
        loc = self.view.content_locations(2)
        assert 4 == len(loc)
        assert 2 in loc
        assert 4 in loc
        assert "s" in loc
        assert 3 in loc
        assert 5 not in loc
        summary = self.collector.session_summary()
        exp_req_hops = [(1, 3), (3, 2)]
        exp_cont_hops = [(2, 3), (3, 1)]
        assert set(exp_req_hops) == set(summary['request_hops'])
        assert set(exp_cont_hops) == set(summary['content_hops'])
        assert 2 == summary['serving_node']
        hr.process_event(1, 1, 2, True)
        loc = self.view.content_locations(2)
        assert 4 == len(loc)
        assert 2 in loc
        assert 4 in loc
        assert "s" in loc
        assert 3 in loc
        assert 5 not in loc
        summary = self.collector.session_summary()
        exp_req_hops = [(1, 3)]
        exp_cont_hops = [(3, 1)]
        assert set(exp_req_hops) == set(summary['request_hops'])
        assert set(exp_cont_hops) == set(summary['content_hops'])
        assert 3 == summary['serving_node']

    def test_lcd(self):
        hr = strategy.NearestReplicaRouting(self.view, self.controller, metacaching='LCD')
        # receiver 0 requests 2, expect miss
        hr.process_event(1, 0, 2, True)
        loc = self.view.content_locations(2)
        assert 2 == len(loc)
        assert 2 not in loc
        assert 4 in loc
        assert "s" in loc
        assert 3 not in loc
        assert 5 not in loc
        summary = self.collector.session_summary()
        exp_req_hops = [(0, 2), (2, 4), (4, "s")]
        exp_cont_hops = [("s", 4), (4, 2), (2, 0)]
        assert set(exp_req_hops) == set(summary['request_hops'])
        assert set(exp_cont_hops) == set(summary['content_hops'])
        assert "s" == summary['serving_node']
        hr.process_event(1, 0, 2, True)
        loc = self.view.content_locations(2)
        assert 3 == len(loc)
        assert 2 in loc
        assert 4 in loc
        assert "s" in loc
        assert 3 not in loc
        assert 5 not in loc
        summary = self.collector.session_summary()
        exp_req_hops = [(0, 2), (2, 4)]
        exp_cont_hops = [(4, 2), (2, 0)]
        assert set(exp_req_hops) == set(summary['request_hops'])
        assert set(exp_cont_hops) == set(summary['content_hops'])
        assert 4 == summary['serving_node']
        hr.process_event(1, 1, 2, True)
        loc = self.view.content_locations(2)
        assert 4 == len(loc)
        assert 2 in loc
        assert 4 in loc
        assert "s" in loc
        assert 3 in loc
        assert 5 not in loc
        summary = self.collector.session_summary()
        exp_req_hops = [(1, 3), (3, 2)]
        exp_cont_hops = [(2, 3), (3, 1)]
        assert set(exp_req_hops) == set(summary['request_hops'])
        assert set(exp_cont_hops) == set(summary['content_hops'])
        assert 2 == summary['serving_node']
        hr.process_event(1, 1, 2, True)
        loc = self.view.content_locations(2)
        assert 4 == len(loc)
        assert 2 in loc
        assert 4 in loc
        assert "s" in loc
        assert 3 in loc
        assert 5 not in loc
        summary = self.collector.session_summary()
        exp_req_hops = [(1, 3)]
        exp_cont_hops = [(3, 1)]
        assert set(exp_req_hops) == set(summary['request_hops'])
        assert set(exp_cont_hops) == set(summary['content_hops'])
        assert 3 == summary['serving_node']
