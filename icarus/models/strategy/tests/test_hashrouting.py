import networkx as nx
import fnss

from icarus.scenarios import IcnTopology
import icarus.models as strategy
from icarus.execution import NetworkModel, NetworkView, NetworkController, DummyCollector


class TestHashroutingEdge(object):

    @classmethod
    def topology(cls):
        #
        #            4 - 5
        #           /     \
        #  r ---- 1 -- 2 -- 3 ---- s
        #
        topology = IcnTopology()
        nx.add_path(topology, ["r", 1, 2, 3, "s"])
        nx.add_path(topology, [1, 4, 5, 3])
        fnss.add_stack(topology, "r", "receiver")
        fnss.add_stack(topology, "s", "source", {'contents': list(range(1, 61))})
        for v in (1, 2, 3, 4, 5):
            fnss.add_stack(topology, v, "router", {"cache_size": 4})
        topology.graph['icr_candidates'] = {1, 2, 3, 4, 5}
        return topology

    def setup_method(self):
        topology = self.topology()
        model = NetworkModel(topology, cache_policy={'name': 'FIFO'})
        self.view = NetworkView(model)
        self.controller = NetworkController(model)
        self.collector = DummyCollector(self.view)
        self.controller.attach_collector(self.collector)

    def test_hashrouting_symmetric_edge(self):
        hr = strategy.HashroutingEdge(self.view, self.controller, 'SYMM', 0.25)
        hr.authoritative_cache = lambda x: ((x - 1) % 5) + 1
        # At time 1, request content 4
        hr.process_event(1, "r", 4, True)
        loc = self.view.content_locations(4)
        assert "s" in loc
        assert 4 in loc
        assert self.view.local_cache_lookup(1, 4)
        assert not self.view.local_cache_lookup(2, 4)
        assert not self.view.local_cache_lookup(3, 4)
        summary = self.collector.session_summary()
        exp_req_hops = [("r", 1), (1, 4), (4, 5), (5, 3), (3, "s")]
        exp_cont_hops = [("s", 3), (3, 5), (5, 4), (4, 1), (1, "r")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert set(exp_req_hops) == set(req_hops)
        assert set(exp_cont_hops) == set(cont_hops)
        assert "s" == summary['serving_node']
        # Let's request it again to make sure we have hit from edge cache
        hr.process_event(1, "r", 4, True)
        loc = self.view.content_locations(4)
        assert "s" in loc
        assert 4 in loc
        assert self.view.local_cache_lookup(1, 4)
        assert not self.view.local_cache_lookup(2, 4)
        assert not self.view.local_cache_lookup(3, 4)
        summary = self.collector.session_summary()
        exp_req_hops = [("r", 1)]
        exp_cont_hops = [(1, "r")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert set(exp_req_hops) == set(req_hops)
        assert set(exp_cont_hops) == set(cont_hops)
        assert 1 == summary['serving_node']
        # Now request content 8 which should replace 4 in the local cache of 1
        # but not 3, because 8 would take space in 3's coordinated ratio
        hr.process_event(1, "r", 8, True)
        loc = self.view.content_locations(8)
        assert "s" in loc
        assert 3 in loc
        assert self.view.local_cache_lookup(1, 8)
        assert not self.view.local_cache_lookup(2, 8)
        assert not self.view.local_cache_lookup(3, 8)
        summary = self.collector.session_summary()
        exp_req_hops = [("r", 1), (1, 2), (2, 3), (3, "s")]
        exp_cont_hops = [("s", 3), (3, 2), (2, 1), (1, "r")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert set(exp_req_hops) == set(req_hops)
        assert set(exp_cont_hops) == set(cont_hops)
        assert "s" == summary['serving_node']
        # Verify where 4 is still stored
        assert not self.view.local_cache_lookup(1, 4)
        assert not self.view.local_cache_lookup(2, 4)
        assert not self.view.local_cache_lookup(3, 4)
        # Request again 4
        hr.process_event(1, "r", 4, True)
        loc = self.view.content_locations(4)
        assert "s" in loc
        assert 4 in loc
        assert self.view.local_cache_lookup(1, 4)
        assert not self.view.local_cache_lookup(2, 4)
        assert not self.view.local_cache_lookup(3, 4)
        summary = self.collector.session_summary()
        exp_req_hops = [("r", 1), (1, 4)]
        exp_cont_hops = [(4, 1), (1, "r")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert set(exp_req_hops) == set(req_hops)
        assert set(exp_cont_hops) == set(cont_hops)
        assert 4 == summary['serving_node']

    def test_hashrouting_symmetric_edge_zero_local(self):
        hr = strategy.HashroutingEdge(self.view, self.controller, 'SYMM', 0)
        hr.authoritative_cache = lambda x: ((x - 1) % 5) + 1
        # At time 1, request content 4
        hr.process_event(1, "r", 4, True)
        loc = self.view.content_locations(4)
        assert "s" in loc
        assert 4 in loc
        assert not self.view.local_cache_lookup(1, 4)
        assert not self.view.local_cache_lookup(2, 4)
        assert not self.view.local_cache_lookup(3, 4)
        summary = self.collector.session_summary()
        exp_req_hops = [("r", 1), (1, 4), (4, 5), (5, 3), (3, "s")]
        exp_cont_hops = [("s", 3), (3, 5), (5, 4), (4, 1), (1, "r")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert set(exp_req_hops) == set(req_hops)
        assert set(exp_cont_hops) == set(cont_hops)
        assert "s" == summary['serving_node']
        # Let's request it again to make sure we have hit from edge cache
        hr.process_event(1, "r", 4, True)
        loc = self.view.content_locations(4)
        assert "s" in loc
        assert 4 in loc
        assert not self.view.local_cache_lookup(1, 4)
        assert not self.view.local_cache_lookup(2, 4)
        assert not self.view.local_cache_lookup(3, 4)
        summary = self.collector.session_summary()
        exp_req_hops = [("r", 1), (1, 4)]
        exp_cont_hops = [(4, 1), (1, "r")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert set(exp_req_hops) == set(req_hops)
        assert set(exp_cont_hops) == set(cont_hops)
        assert 4 == summary['serving_node']
        # Now request content 8 which should replace 4 in the local cache of 1
        # but not 3, because 8 would take space in 3's coordinated ratio
        hr.process_event(1, "r", 8, True)
        loc = self.view.content_locations(8)
        assert "s" in loc
        assert 3 in loc
        assert not self.view.local_cache_lookup(1, 8)
        assert not self.view.local_cache_lookup(2, 8)
        assert not self.view.local_cache_lookup(3, 8)
        summary = self.collector.session_summary()
        exp_req_hops = [("r", 1), (1, 2), (2, 3), (3, "s")]
        exp_cont_hops = [("s", 3), (3, 2), (2, 1), (1, "r")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert set(exp_req_hops) == set(req_hops)
        assert set(exp_cont_hops) == set(cont_hops)
        assert "s" == summary['serving_node']
        # Verify where 4 is still stored
        assert not self.view.local_cache_lookup(1, 4)
        assert not self.view.local_cache_lookup(2, 4)
        assert not self.view.local_cache_lookup(3, 4)
        # Request again 4
        hr.process_event(1, "r", 4, True)
        loc = self.view.content_locations(4)
        assert "s" in loc
        assert 4 in loc
        assert not self.view.local_cache_lookup(1, 4)
        assert not self.view.local_cache_lookup(2, 4)
        assert not self.view.local_cache_lookup(3, 4)
        summary = self.collector.session_summary()
        exp_req_hops = [("r", 1), (1, 4)]
        exp_cont_hops = [(4, 1), (1, "r")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert set(exp_req_hops) == set(req_hops)
        assert set(exp_cont_hops) == set(cont_hops)
        assert 4 == summary['serving_node']

    def test_hashrouting_symmetric_edge_zero_coordinated(self):
        hr = strategy.HashroutingEdge(self.view, self.controller, 'SYMM', 1)
        hr.authoritative_cache = lambda x: ((x - 1) % 5) + 1
        # At time 1, request content 4
        hr.process_event(1, "r", 4, True)
        loc = self.view.content_locations(4)
        assert "s" in loc
        assert 4 not in loc
        assert self.view.local_cache_lookup(1, 4)
        assert not self.view.local_cache_lookup(2, 4)
        assert not self.view.local_cache_lookup(3, 4)
        summary = self.collector.session_summary()
        exp_req_hops = [("r", 1), (1, 4), (4, 5), (5, 3), (3, "s")]
        exp_cont_hops = [("s", 3), (3, 5), (5, 4), (4, 1), (1, "r")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert set(exp_req_hops) == set(req_hops)
        assert set(exp_cont_hops) == set(cont_hops)
        assert "s" == summary['serving_node']
        # Let's request it again to make sure we have hit from edge cache
        hr.process_event(1, "r", 4, True)
        loc = self.view.content_locations(4)
        assert "s" in loc
        assert 4 not in loc
        assert self.view.local_cache_lookup(1, 4)
        assert not self.view.local_cache_lookup(2, 4)
        assert not self.view.local_cache_lookup(3, 4)
        summary = self.collector.session_summary()
        exp_req_hops = [("r", 1)]
        exp_cont_hops = [(1, "r")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert set(exp_req_hops) == set(req_hops)
        assert set(exp_cont_hops) == set(cont_hops)
        assert 1 == summary['serving_node']
        # Now request content 8 which should replace 4 in the local cache of 1
        # but not 3, because 8 would take space in 3's coordinated ratio
        hr.process_event(1, "r", 8, True)
        loc = self.view.content_locations(8)
        assert "s" in loc
        assert 3 not in loc
        assert self.view.local_cache_lookup(1, 8)
        assert not self.view.local_cache_lookup(2, 8)
        assert not self.view.local_cache_lookup(3, 8)
        summary = self.collector.session_summary()
        exp_req_hops = [("r", 1), (1, 2), (2, 3), (3, "s")]
        exp_cont_hops = [("s", 3), (3, 2), (2, 1), (1, "r")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert set(exp_req_hops) == set(req_hops)
        assert set(exp_cont_hops) == set(cont_hops)
        assert "s" == summary['serving_node']
        # Verify where 4 is still stored
        assert self.view.local_cache_lookup(1, 4)
        assert not self.view.local_cache_lookup(2, 4)
        assert not self.view.local_cache_lookup(3, 4)
        # Request again 4
        hr.process_event(1, "r", 4, True)
        loc = self.view.content_locations(4)
        assert "s" in loc
        assert 4 not in loc
        assert self.view.local_cache_lookup(1, 4)
        assert not self.view.local_cache_lookup(2, 4)
        assert not self.view.local_cache_lookup(3, 4)
        summary = self.collector.session_summary()
        exp_req_hops = [("r", 1)]
        exp_cont_hops = [(1, "r")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert set(exp_req_hops) == set(req_hops)
        assert set(exp_cont_hops) == set(cont_hops)
        assert 1 == summary['serving_node']


class TestHashroutingOnPath(object):

    @classmethod
    def topology(cls):
        #
        #            4 - 5
        #           /     \
        #  r ---- 1 -- 2 -- 3 ---- s
        #
        topology = IcnTopology()
        nx.add_path(topology, ["r", 1, 2, 3, "s"])
        nx.add_path(topology, [1, 4, 5, 3])
        fnss.add_stack(topology, "r", "receiver")
        fnss.add_stack(topology, "s", "source", {'contents': list(range(1, 61))})
        for v in (1, 2, 3, 4, 5):
            fnss.add_stack(topology, v, "router", {"cache_size": 4})
        topology.graph['icr_candidates'] = {1, 2, 3, 4, 5}
        return topology

    def setup_method(self):
        topology = self.topology()
        model = NetworkModel(topology, cache_policy={'name': 'FIFO'})
        self.view = NetworkView(model)
        self.controller = NetworkController(model)
        self.collector = DummyCollector(self.view)
        self.controller.attach_collector(self.collector)

    def test_hashrouting_symmetric(self):
        hr = strategy.HashroutingOnPath(self.view, self.controller, 'SYMM', 0.25)
        hr.authoritative_cache = lambda x: ((x - 1) % 5) + 1
        # At time 1, request content 4
        hr.process_event(1, "r", 4, True)
        loc = self.view.content_locations(4)
        assert "s" in loc
        assert 4 in loc
        assert self.view.local_cache_lookup(1, 4)
        assert not self.view.local_cache_lookup(2, 4)
        assert self.view.local_cache_lookup(3, 4)
        summary = self.collector.session_summary()
        exp_req_hops = [("r", 1), (1, 4), (4, 5), (5, 3), (3, "s")]
        exp_cont_hops = [("s", 3), (3, 5), (5, 4), (4, 1), (1, "r")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert set(exp_req_hops) == set(req_hops)
        assert set(exp_cont_hops) == set(cont_hops)
        assert "s" == summary['serving_node']
        # Let's request it again to make sure we have hit from edge cache
        hr.process_event(1, "r", 4, True)
        loc = self.view.content_locations(4)
        assert "s" in loc
        assert 4 in loc
        assert self.view.local_cache_lookup(1, 4)
        assert not self.view.local_cache_lookup(2, 4)
        assert self.view.local_cache_lookup(3, 4)
        summary = self.collector.session_summary()
        exp_req_hops = [("r", 1)]
        exp_cont_hops = [(1, "r")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert set(exp_req_hops) == set(req_hops)
        assert set(exp_cont_hops) == set(cont_hops)
        assert 1 == summary['serving_node']
        # Now request content 8 which should replace 4 in the local cache of 1
        # but not 3, because 8 would take space in 3's coordinated ratio
        hr.process_event(1, "r", 8, True)
        loc = self.view.content_locations(8)
        assert "s" in loc
        assert 3 in loc
        assert self.view.local_cache_lookup(1, 8)
        assert self.view.local_cache_lookup(2, 8)
        assert not self.view.local_cache_lookup(3, 8)
        summary = self.collector.session_summary()
        exp_req_hops = [("r", 1), (1, 2), (2, 3), (3, "s")]
        exp_cont_hops = [("s", 3), (3, 2), (2, 1), (1, "r")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert set(exp_req_hops) == set(req_hops)
        assert set(exp_cont_hops) == set(cont_hops)
        assert "s" == summary['serving_node']
        # Verify where 4 is still stored
        assert not self.view.local_cache_lookup(1, 4)
        assert not self.view.local_cache_lookup(2, 4)
        assert self.view.local_cache_lookup(3, 4)
        # Request again 4
        hr.process_event(1, "r", 4, True)
        loc = self.view.content_locations(4)
        assert "s" in loc
        assert 4 in loc
        assert self.view.local_cache_lookup(1, 4)
        assert not self.view.local_cache_lookup(2, 4)
        assert self.view.local_cache_lookup(3, 4)
        summary = self.collector.session_summary()
        exp_req_hops = [("r", 1), (1, 4)]
        exp_cont_hops = [(4, 1), (1, "r")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert set(exp_req_hops) == set(req_hops)
        assert set(exp_cont_hops) == set(cont_hops)
        assert 4 == summary['serving_node']

    def test_hashrouting_symmetric_zero_local(self):
        hr = strategy.HashroutingOnPath(self.view, self.controller, 'SYMM', 0)
        hr.authoritative_cache = lambda x: ((x - 1) % 5) + 1
        # At time 1, request content 4
        hr.process_event(1, "r", 4, True)
        loc = self.view.content_locations(4)
        assert "s" in loc
        assert 4 in loc
        assert not self.view.local_cache_lookup(1, 4)
        assert not self.view.local_cache_lookup(2, 4)
        assert not self.view.local_cache_lookup(3, 4)
        summary = self.collector.session_summary()
        exp_req_hops = [("r", 1), (1, 4), (4, 5), (5, 3), (3, "s")]
        exp_cont_hops = [("s", 3), (3, 5), (5, 4), (4, 1), (1, "r")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert set(exp_req_hops) == set(req_hops)
        assert set(exp_cont_hops) == set(cont_hops)
        assert "s" == summary['serving_node']
        # Let's request it again to make sure we have hit from edge cache
        hr.process_event(1, "r", 4, True)
        loc = self.view.content_locations(4)
        assert "s" in loc
        assert 4 in loc
        assert not self.view.local_cache_lookup(1, 4)
        assert not self.view.local_cache_lookup(2, 4)
        assert not self.view.local_cache_lookup(3, 4)
        summary = self.collector.session_summary()
        exp_req_hops = [("r", 1), (1, 4)]
        exp_cont_hops = [(4, 1), (1, "r")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert set(exp_req_hops) == set(req_hops)
        assert set(exp_cont_hops) == set(cont_hops)
        assert 4 == summary['serving_node']
        # Now request content 6 which should replace 4 in the local cache of 1
        # but not 3, because 6 would take space in 3's coordinated ratio
        hr.process_event(1, "r", 8, True)
        loc = self.view.content_locations(8)
        assert "s" in loc
        assert 3 in loc
        assert not self.view.local_cache_lookup(1, 8)
        assert not self.view.local_cache_lookup(2, 8)
        assert not self.view.local_cache_lookup(3, 8)
        summary = self.collector.session_summary()
        exp_req_hops = [("r", 1), (1, 2), (2, 3), (3, "s")]
        exp_cont_hops = [("s", 3), (3, 2), (2, 1), (1, "r")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert set(exp_req_hops) == set(req_hops)
        assert set(exp_cont_hops) == set(cont_hops)
        assert "s" == summary['serving_node']
        # Verify where 4 is still stored
        assert not self.view.local_cache_lookup(1, 4)
        assert not self.view.local_cache_lookup(2, 4)
        assert not self.view.local_cache_lookup(3, 4)
        # Request again 4
        hr.process_event(1, "r", 4, True)
        loc = self.view.content_locations(4)
        assert "s" in loc
        assert 4 in loc
        assert not self.view.local_cache_lookup(1, 4)
        assert not self.view.local_cache_lookup(2, 4)
        assert not self.view.local_cache_lookup(3, 4)
        summary = self.collector.session_summary()
        exp_req_hops = [("r", 1), (1, 4)]
        exp_cont_hops = [(4, 1), (1, "r")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert set(exp_req_hops) == set(req_hops)
        assert set(exp_cont_hops) == set(cont_hops)
        assert 4 == summary['serving_node']

    def test_hashrouting_symmetric_zero_coordinated(self):
        hr = strategy.HashroutingOnPath(self.view, self.controller, 'SYMM', 1)
        hr.authoritative_cache = lambda x: ((x - 1) % 5) + 1
        # At time 1, request content 4
        hr.process_event(1, "r", 4, True)
        loc = self.view.content_locations(4)
        assert "s" in loc
        assert 4 not in loc
        assert self.view.local_cache_lookup(1, 4)
        assert not self.view.local_cache_lookup(2, 4)
        assert self.view.local_cache_lookup(3, 4)
        summary = self.collector.session_summary()
        exp_req_hops = [("r", 1), (1, 4), (4, 5), (5, 3), (3, "s")]
        exp_cont_hops = [("s", 3), (3, 5), (5, 4), (4, 1), (1, "r")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert set(exp_req_hops) == set(req_hops)
        assert set(exp_cont_hops) == set(cont_hops)
        assert "s" == summary['serving_node']
        # Let's request it again to make sure we have hit from edge cache
        hr.process_event(1, "r", 4, True)
        loc = self.view.content_locations(4)
        assert "s" in loc
        assert 4 not in loc
        assert self.view.local_cache_lookup(1, 4)
        assert not self.view.local_cache_lookup(2, 4)
        assert self.view.local_cache_lookup(3, 4)
        summary = self.collector.session_summary()
        exp_req_hops = [("r", 1)]
        exp_cont_hops = [(1, "r")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert set(exp_req_hops) == set(req_hops)
        assert set(exp_cont_hops) == set(cont_hops)
        assert 1 == summary['serving_node']
        # Now request content 6 which should replace 4 in the local cache of 1
        # but not 3, because 6 would take space in 3's coordinated ratio
        hr.process_event(1, "r", 8, True)
        loc = self.view.content_locations(8)
        assert "s" in loc
        assert 3 not in loc
        assert self.view.local_cache_lookup(1, 8)
        assert self.view.local_cache_lookup(2, 8)
        # Note: this assertion below is false, because we never store items
        # for the authoritative cache in the uncoordinated section, even if
        # the coordinated cache is empty
        assert not self.view.local_cache_lookup(3, 7)
        summary = self.collector.session_summary()
        exp_req_hops = [("r", 1), (1, 2), (2, 3), (3, "s")]
        exp_cont_hops = [("s", 3), (3, 2), (2, 1), (1, "r")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert set(exp_req_hops) == set(req_hops)
        assert set(exp_cont_hops) == set(cont_hops)
        assert "s" == summary['serving_node']
        # Verify where 4 is still stored
        assert self.view.local_cache_lookup(1, 4)
        assert not self.view.local_cache_lookup(2, 4)
        assert self.view.local_cache_lookup(3, 4)
        # Request again 4
        hr.process_event(1, "r", 4, True)
        loc = self.view.content_locations(4)
        assert "s" in loc
        assert 4 not in loc
        assert self.view.local_cache_lookup(1, 4)
        assert not self.view.local_cache_lookup(2, 4)
        assert self.view.local_cache_lookup(3, 4)
        summary = self.collector.session_summary()
        exp_req_hops = [("r", 1)]
        exp_cont_hops = [(1, "r")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert set(exp_req_hops) == set(req_hops)
        assert set(exp_cont_hops) == set(cont_hops)
        assert 1 == summary['serving_node']


class TestHashroutingClustered(object):

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
        nx.add_path(topology, ['RCV', 1, 2, 4, 5, 'SRC'])
        nx.add_path(topology, [2, 3, 1])
        nx.add_path(topology, [5, 6, 4])
        fnss.set_delays_constant(topology, 1, 'ms')
        fnss.set_delays_constant(topology, 15, 'ms', [(2, 4)])
        caches = (1, 2, 3, 4, 5, 6)
        contents = [1, 2, 3]
        clusters = [{1, 2, 3}, {4, 5, 6}]
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

    def setup_method(self):
        topology = self.clustered_topology()
        self.model = NetworkModel(topology, cache_policy={'name': 'FIFO'})
        self.view = NetworkView(self.model)
        self.controller = NetworkController(self.model)
        self.collector = DummyCollector(self.view)
        self.controller.attach_collector(self.collector)

    def test_hashrouting_symmetric_lce(self):
        hr = strategy.HashroutingClustered(self.view, self.controller,
                                           intra_routing='SYMM',
                                           inter_routing='LCE')
        hr.authoritative_cache = lambda x, cluster: cluster * 3 + x
        # At time 1, receiver 0 requests content 2
        hr.process_event(1, "RCV", 3, True)
        loc = self.view.content_locations(3)
        assert len(loc) == 3
        assert "SRC" in loc
        assert 3 in loc
        assert 6 in loc
        summary = self.collector.session_summary()
        exp_req_hops = [("RCV", 1), (1, 3), (3, 2), (2, 4), (4, 6), (6, 5), (5, "SRC")]
        exp_cont_hops = [("SRC", 5), (5, 6), (6, 4), (4, 2), (2, 3), (3, 1), (1, "RCV")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert set(exp_req_hops) == set(req_hops)
        assert set(exp_cont_hops) == set(cont_hops)
        assert summary['serving_node'] == "SRC"
        # Expect hit from first cluster
        hr.process_event(1, "RCV", 3, True)
        loc = self.view.content_locations(3)
        assert len(loc) == 3
        assert "SRC" in loc
        assert 3 in loc
        assert 6 in loc
        summary = self.collector.session_summary()
        exp_req_hops = [("RCV", 1), (1, 3)]
        exp_cont_hops = [(3, 1), (1, "RCV")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert set(exp_req_hops) == set(req_hops)
        assert set(exp_cont_hops) == set(cont_hops)
        assert summary['serving_node'] == 3
        # Delete entry on first cluster, expect hit on second cluster
        self.model.cache[3].remove(3)
        hr.process_event(1, "RCV", 3, True)
        loc = self.view.content_locations(3)
        assert len(loc) == 3
        assert "SRC" in loc
        assert 3 in loc
        assert 6 in loc
        summary = self.collector.session_summary()
        exp_req_hops = [("RCV", 1), (1, 3), (3, 2), (2, 4), (4, 6)]
        exp_cont_hops = [(6, 4), (4, 2), (2, 3), (3, 1), (1, "RCV")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert set(exp_req_hops) == set(req_hops)
        assert set(exp_cont_hops) == set(cont_hops)
        assert summary['serving_node'] == 6

    def test_hashrouting_asymmetric_lce(self):
        hr = strategy.HashroutingClustered(self.view, self.controller,
                                           intra_routing='ASYMM',
                                           inter_routing='LCE')
        hr.authoritative_cache = lambda x, cluster: cluster * 3 + x
        # Expect miss
        hr.process_event(1, "RCV", 3, True)
        loc = self.view.content_locations(3)
        assert len(loc) == 1
        assert "SRC" in loc
        assert 3 not in loc
        assert 6 not in loc
        summary = self.collector.session_summary()
        exp_req_hops = [("RCV", 1), (1, 3), (3, 2), (2, 4), (4, 6), (6, 5), (5, "SRC")]
        exp_cont_hops = [("SRC", 5), (5, 4), (4, 2), (2, 1), (1, "RCV")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert set(exp_req_hops) == set(req_hops)
        assert set(exp_cont_hops) == set(cont_hops)
        assert summary['serving_node'] == "SRC"
        # Expect miss again, but this time caches will be populated
        hr.process_event(1, "RCV", 2, True)
        loc = self.view.content_locations(2)
        assert len(loc) == 3
        assert "SRC" in loc
        assert 2 in loc
        assert 5 in loc
        summary = self.collector.session_summary()
        exp_req_hops = [("RCV", 1), (1, 2), (2, 4), (4, 5), (5, 'SRC')]
        exp_cont_hops = [("SRC", 5), (5, 4), (4, 2), (2, 1), (1, "RCV")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert set(exp_req_hops) == set(req_hops)
        assert set(exp_cont_hops) == set(cont_hops)
        assert summary['serving_node'] == "SRC"
        # Expect hit
        hr.process_event(1, "RCV", 2, True)
        loc = self.view.content_locations(2)
        assert len(loc) == 3
        assert "SRC" in loc
        assert 2 in loc
        assert 5 in loc
        summary = self.collector.session_summary()
        exp_req_hops = [("RCV", 1), (1, 2)]
        exp_cont_hops = [(2, 1), (1, "RCV")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert set(exp_req_hops) == set(req_hops)
        assert set(exp_cont_hops) == set(cont_hops)
        assert summary['serving_node'] == 2

    def test_hashrouting_multicast_lce(self):
        hr = strategy.HashroutingClustered(self.view, self.controller,
                                           intra_routing='MULTICAST',
                                           inter_routing='LCE')
        hr.authoritative_cache = lambda x, cluster: cluster * 3 + x
        # At time 1, receiver 0 requests content 2
        hr.process_event(1, "RCV", 3, True)
        loc = self.view.content_locations(3)
        assert len(loc) == 3
        assert "SRC" in loc
        assert 3 in loc
        assert 6 in loc
        summary = self.collector.session_summary()
        exp_req_hops = [("RCV", 1), (1, 3), (3, 2), (2, 4), (4, 6), (6, 5), (5, "SRC")]
        exp_cont_hops = [("SRC", 5), (5, 6), (5, 4), (4, 2), (2, 3), (2, 1), (1, "RCV")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert set(exp_req_hops) == set(req_hops)
        assert set(exp_cont_hops) == set(cont_hops)
        assert summary['serving_node'] == "SRC"
        # Expect hit from first cluster
        hr.process_event(1, "RCV", 3, True)
        loc = self.view.content_locations(3)
        assert len(loc) == 3
        assert "SRC" in loc
        assert 3 in loc
        assert 6 in loc
        summary = self.collector.session_summary()
        exp_req_hops = [("RCV", 1), (1, 3)]
        exp_cont_hops = [(3, 1), (1, "RCV")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert set(exp_req_hops) == set(req_hops)
        assert set(exp_cont_hops) == set(cont_hops)
        assert summary['serving_node'] == 3
        # Delete entry on first cluster, expect hit on second cluster
        self.model.cache[3].remove(3)
        hr.process_event(1, "RCV", 3, True)
        loc = self.view.content_locations(3)
        assert len(loc) == 3
        assert "SRC" in loc
        assert 3 in loc
        assert 6 in loc
        summary = self.collector.session_summary()
        exp_req_hops = [("RCV", 1), (1, 3), (3, 2), (2, 4), (4, 6)]
        exp_cont_hops = [(6, 4), (4, 2), (2, 3), (2, 1), (1, "RCV")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert set(exp_req_hops) == set(req_hops)
        assert set(exp_cont_hops) == set(cont_hops)
        assert summary['serving_node'] == 6

    def test_hashrouting_symmetric_edge(self):
        hr = strategy.HashroutingClustered(self.view, self.controller,
                                           intra_routing='SYMM',
                                           inter_routing='EDGE')
        hr.authoritative_cache = lambda x, cluster: cluster * 3 + x
        # At time 1, receiver 0 requests content 2
        hr.process_event(1, "RCV", 3, True)
        loc = self.view.content_locations(3)
        assert 2 == len(loc)
        assert "SRC" in loc
        assert 3 in loc
        assert 6 not in loc
        summary = self.collector.session_summary()
        exp_req_hops = [("RCV", 1), (1, 3), (3, 2), (2, 4), (4, 5), (5, "SRC")]
        exp_cont_hops = [("SRC", 5), (5, 4), (4, 2), (2, 3), (3, 1), (1, "RCV")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert set(exp_req_hops) == set(req_hops)
        assert set(exp_cont_hops) == set(cont_hops)
        assert summary['serving_node'] == "SRC"
        # Expect hit from first cluster
        hr.process_event(1, "RCV", 3, True)
        loc = self.view.content_locations(3)
        assert len(loc) == 2
        assert "SRC" in loc
        assert 3 in loc
        assert 6 not in loc
        summary = self.collector.session_summary()
        exp_req_hops = [("RCV", 1), (1, 3)]
        exp_cont_hops = [(3, 1), (1, "RCV")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert set(exp_req_hops) == set(req_hops)
        assert set(exp_cont_hops) == set(cont_hops)
        assert summary['serving_node'] == 3
        # Delete entry on first cluster, expect miss
        self.model.cache[3].remove(3)
        hr.process_event(1, "RCV", 3, True)
        loc = self.view.content_locations(3)
        assert len(loc) == 2
        assert "SRC" in loc
        assert 3 in loc
        assert 6 not in loc
        summary = self.collector.session_summary()
        exp_req_hops = [("RCV", 1), (1, 3), (3, 2), (2, 4), (4, 5), (5, "SRC")]
        exp_cont_hops = [("SRC", 5), (5, 4), (4, 2), (2, 3), (3, 1), (1, "RCV")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert set(exp_req_hops) == set(req_hops)
        assert set(exp_cont_hops) == set(cont_hops)
        assert "SRC" == summary['serving_node']

    def test_hashrouting_asymmetric_edge(self):
        hr = strategy.HashroutingClustered(self.view, self.controller,
                                           intra_routing='ASYMM',
                                           inter_routing='EDGE')
        hr.authoritative_cache = lambda x, cluster: cluster * 3 + x
        # Expect miss
        hr.process_event(1, "RCV", 3, True)
        loc = self.view.content_locations(3)
        assert len(loc) == 1
        assert "SRC" in loc
        assert 3 not in loc
        assert 6 not in loc
        summary = self.collector.session_summary()
        exp_req_hops = [("RCV", 1), (1, 3), (3, 2), (2, 4), (4, 5), (5, "SRC")]
        exp_cont_hops = [("SRC", 5), (5, 4), (4, 2), (2, 1), (1, "RCV")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert set(exp_req_hops) == set(req_hops)
        assert set(exp_cont_hops) == set(cont_hops)
        assert summary['serving_node'] == "SRC"
        # Expect miss again, but this time caches will be populated
        hr.process_event(1, "RCV", 2, True)
        loc = self.view.content_locations(2)
        assert len(loc) == 3
        assert "SRC" in loc
        assert 2 in loc
        assert 5 in loc
        summary = self.collector.session_summary()
        exp_req_hops = [("RCV", 1), (1, 2), (2, 4), (4, 5), (5, 'SRC')]
        exp_cont_hops = [("SRC", 5), (5, 4), (4, 2), (2, 1), (1, "RCV")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert set(exp_req_hops) == set(req_hops)
        assert set(exp_cont_hops) == set(cont_hops)
        assert summary['serving_node'] == "SRC"
        # Expect hit
        hr.process_event(1, "RCV", 2, True)
        loc = self.view.content_locations(2)
        assert len(loc) == 3
        assert "SRC" in loc
        assert 2 in loc
        assert 5 in loc
        summary = self.collector.session_summary()
        exp_req_hops = [("RCV", 1), (1, 2)]
        exp_cont_hops = [(2, 1), (1, "RCV")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert set(exp_req_hops) == set(req_hops)
        assert set(exp_cont_hops) == set(cont_hops)
        assert summary['serving_node'] == 2

    def test_hashrouting_multicast_edge(self):
        hr = strategy.HashroutingClustered(self.view, self.controller,
                                           intra_routing='MULTICAST',
                                           inter_routing='EDGE')
        hr.authoritative_cache = lambda x, cluster: cluster * 3 + x
        # At time 1, receiver 0 requests content 2
        hr.process_event(1, "RCV", 3, True)
        loc = self.view.content_locations(3)
        assert len(loc) == 2
        assert "SRC" in loc
        assert 3 in loc
        assert 6 not in loc
        summary = self.collector.session_summary()
        exp_req_hops = [("RCV", 1), (1, 3), (3, 2), (2, 4), (4, 5), (5, "SRC")]
        exp_cont_hops = [("SRC", 5), (5, 4), (4, 2), (2, 3), (2, 1), (1, "RCV")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert set(exp_req_hops) == set(req_hops)
        assert set(exp_cont_hops) == set(cont_hops)
        assert summary['serving_node'] == "SRC"
        # Expect hit from first cluster
        hr.process_event(1, "RCV", 3, True)
        loc = self.view.content_locations(3)
        assert len(loc) == 2
        assert "SRC" in loc
        assert 3 in loc
        assert 6 not in loc
        summary = self.collector.session_summary()
        exp_req_hops = [("RCV", 1), (1, 3)]
        exp_cont_hops = [(3, 1), (1, "RCV")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert set(exp_req_hops) == set(req_hops)
        assert set(exp_cont_hops) == set(cont_hops)
        assert summary['serving_node'] == 3
        # Delete entry on first cluster, expect miss
        self.model.cache[3].remove(3)
        hr.process_event(1, "RCV", 3, True)
        loc = self.view.content_locations(3)
        assert 2 == len(loc)
        assert "SRC" in loc
        assert 3 in loc
        assert 6 not in loc
        summary = self.collector.session_summary()
        exp_req_hops = [("RCV", 1), (1, 3), (3, 2), (2, 4), (4, 5), (5, "SRC")]
        exp_cont_hops = [("SRC", 5), (5, 4), (4, 2), (2, 3), (2, 1), (1, "RCV")]
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert set(exp_req_hops) == set(req_hops)
        assert set(exp_cont_hops) == set(cont_hops)
        assert "SRC" == summary['serving_node']


class TestHashrouting(object):

    @classmethod
    def topology(cls):
        """Return topology for testing off-path caching strategies"""
        # Topology sketch
        #
        #      -------- 5 ---------
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

    def setup_method(self):
        topology = self.topology()
        model = NetworkModel(topology, cache_policy={'name': 'FIFO'})
        self.view = NetworkView(model)
        self.controller = NetworkController(model)
        self.collector = DummyCollector(self.view)
        self.controller.attach_collector(self.collector)

    def test_hashrouting_symmetric(self):
        hr = strategy.HashroutingSymmetric(self.view, self.controller)
        hr.authoritative_cache = lambda x: x
        # At time 1, receiver 0 requests content 2
        hr.process_event(1, 0, 2, True)
        loc = self.view.content_locations(2)
        assert len(loc) == 2
        assert 2 in loc
        assert 4 in loc
        summary = self.collector.session_summary()
        exp_req_hops = {(0, 1), (1, 2), (2, 3), (3, 4)}
        exp_cont_hops = {(4, 3), (3, 2), (2, 1), (1, 0)}
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert exp_req_hops == set(req_hops)
        assert exp_cont_hops == set(cont_hops)
        # At time 2 repeat request, expect cache hit
        hr.process_event(2, 0, 2, True)
        loc = self.view.content_locations(2)
        assert len(loc) == 2
        assert 2 in loc
        assert 4 in loc
        summary = self.collector.session_summary()
        exp_req_hops = {(0, 1), (1, 2)}
        exp_cont_hops = {(2, 1), (1, 0)}
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert exp_req_hops == set(req_hops)
        assert exp_cont_hops == set(cont_hops)
        # Now request from node 6, expect hit
        hr.process_event(3, 6, 2, True)
        loc = self.view.content_locations(2)
        assert len(loc) == 2
        assert 2 in loc
        assert 4 in loc
        summary = self.collector.session_summary()
        exp_req_hops = {(6, 2)}
        exp_cont_hops = {(2, 6)}
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert exp_req_hops == set(req_hops)
        assert exp_cont_hops == set(cont_hops)

    def test_hashrouting_asymmetric(self):
        hr = strategy.HashroutingAsymmetric(self.view, self.controller)
        hr.authoritative_cache = lambda x: x
        # At time 1, receiver 0 requests content 2
        hr.process_event(1, 0, 2, True)
        loc = self.view.content_locations(2)
        assert len(loc) == 1
        assert 4 in loc
        summary = self.collector.session_summary()
        exp_req_hops = {(0, 1), (1, 2), (2, 3), (3, 4)}
        exp_cont_hops = {(4, 5), (5, 0)}
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert exp_req_hops == set(req_hops)
        assert exp_cont_hops == set(cont_hops)
        # Now request from node 6, expect miss but cache insertion
        hr.process_event(2, 6, 2, True)
        loc = self.view.content_locations(2)
        assert len(loc) == 2
        assert 2 in loc
        assert 4 in loc
        summary = self.collector.session_summary()
        exp_req_hops = {(6, 2), (2, 3), (3, 4)}
        exp_cont_hops = {(4, 3), (3, 2), (2, 6)}
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert exp_req_hops == set(req_hops)
        assert exp_cont_hops == set(cont_hops)
        # Now request from node 0 again, expect hit
        hr.process_event(3, 0, 2, True)
        loc = self.view.content_locations(2)
        assert len(loc) == 2
        assert 2 in loc
        assert 4 in loc
        summary = self.collector.session_summary()
        exp_req_hops = {(0, 1), (1, 2)}
        exp_cont_hops = {(2, 1), (1, 0)}
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert exp_req_hops == set(req_hops)
        assert exp_cont_hops == set(cont_hops)

    def test_hashrouting_multicast(self):
        hr = strategy.HashroutingMulticast(self.view, self.controller)
        hr.authoritative_cache = lambda x: x
        # At time 1, receiver 0 requests content 2
        hr.process_event(1, 0, 2, True)
        loc = self.view.content_locations(2)
        assert len(loc) == 2
        assert 2 in loc
        assert 4 in loc
        summary = self.collector.session_summary()
        exp_req_hops = {(0, 1), (1, 2), (2, 3), (3, 4)}
        exp_cont_hops = {(4, 3), (3, 2), (4, 5), (5, 0)}
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert exp_req_hops == set(req_hops)
        assert exp_cont_hops == set(cont_hops)
        # At time 2 repeat request, expect cache hit
        hr.process_event(2, 0, 2, True)
        loc = self.view.content_locations(2)
        assert len(loc) == 2
        assert 2 in loc
        assert 4 in loc
        summary = self.collector.session_summary()
        exp_req_hops = {(0, 1), (1, 2)}
        exp_cont_hops = {(2, 1), (1, 0)}
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert exp_req_hops == set(req_hops)
        assert exp_cont_hops == set(cont_hops)
        # Now request from node 6, expect hit
        hr.process_event(3, 6, 2, True)
        loc = self.view.content_locations(2)
        assert len(loc) == 2
        assert 2 in loc
        assert 4 in loc
        summary = self.collector.session_summary()
        exp_req_hops = {(6, 2)}
        exp_cont_hops = {(2, 6)}
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert exp_req_hops == set(req_hops)
        assert exp_cont_hops == set(cont_hops)

    def test_hashrouting_hybrid_am(self):
        hr = strategy.HashroutingHybridAM(self.view, self.controller, max_stretch=0.3)
        hr.authoritative_cache = lambda x: x
        # At time 1, receiver 0 requests content 2, expect asymmetric
        hr.process_event(1, 0, 2, True)
        loc = self.view.content_locations(2)
        assert len(loc) == 1
        assert 4 in loc
        summary = self.collector.session_summary()
        exp_req_hops = {(0, 1), (1, 2), (2, 3), (3, 4)}
        exp_cont_hops = {(4, 5), (5, 0)}
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert exp_req_hops == set(req_hops)
        assert exp_cont_hops == set(cont_hops)
        # At time 2, receiver 0 requests content 3, expect multicast
        hr.process_event(3, 0, 3, True)
        loc = self.view.content_locations(3)
        assert len(loc) == 2
        assert 3 in loc
        assert 4 in loc
        summary = self.collector.session_summary()
        exp_req_hops = {(0, 1), (1, 2), (2, 3), (3, 4)}
        exp_cont_hops = {(4, 5), (5, 0), (4, 3)}
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert exp_req_hops == set(req_hops)
        assert exp_cont_hops == set(cont_hops)
        # At time 3, receiver 0 requests content 5, expect symm = mcast = asymm
        hr.process_event(3, 0, 5, True)
        loc = self.view.content_locations(5)
        assert len(loc) == 2
        assert 5 in loc
        assert 4 in loc
        summary = self.collector.session_summary()
        exp_req_hops = {(0, 5), (5, 4)}
        exp_cont_hops = {(4, 5), (5, 0)}
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert exp_req_hops == set(req_hops)
        assert exp_cont_hops == set(cont_hops)

    def test_hashrouting_hybrid_am_max_stretch_0(self):
        hr = strategy.HashroutingHybridAM(self.view, self.controller, max_stretch=0)
        hr.authoritative_cache = lambda x: x
        # At time 1, receiver 0 requests content 2
        hr.process_event(1, 0, 2, True)
        loc = self.view.content_locations(2)
        assert len(loc) == 1
        assert 4 in loc
        summary = self.collector.session_summary()
        exp_req_hops = {(0, 1), (1, 2), (2, 3), (3, 4)}
        exp_cont_hops = {(4, 5), (5, 0)}
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert exp_req_hops == set(req_hops)
        assert exp_cont_hops == set(cont_hops)
        # Now request from node 6, expect miss but cache insertion
        hr.process_event(2, 6, 2, True)
        loc = self.view.content_locations(2)
        assert len(loc) == 2
        assert 2 in loc
        assert 4 in loc
        summary = self.collector.session_summary()
        exp_req_hops = {(6, 2), (2, 3), (3, 4)}
        exp_cont_hops = {(4, 3), (3, 2), (2, 6)}
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert exp_req_hops == set(req_hops)
        assert exp_cont_hops == set(cont_hops)
        # Now request from node 0 again, expect hit
        hr.process_event(3, 0, 2, True)
        loc = self.view.content_locations(2)
        assert len(loc) == 2
        assert 2 in loc
        assert 4 in loc
        summary = self.collector.session_summary()
        exp_req_hops = {(0, 1), (1, 2)}
        exp_cont_hops = {(2, 1), (1, 0)}
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert exp_req_hops == set(req_hops)
        assert exp_cont_hops == set(cont_hops)

    def test_hashrouting_hybrid_am_max_stretch_1(self):
        hr = strategy.HashroutingHybridAM(self.view, self.controller, max_stretch=1.0)
        hr.authoritative_cache = lambda x: x
        # At time 1, receiver 0 requests content 2
        hr.process_event(1, 0, 2, True)
        loc = self.view.content_locations(2)
        assert len(loc) == 2
        assert 2 in loc
        assert 4 in loc
        summary = self.collector.session_summary()
        exp_req_hops = {(0, 1), (1, 2), (2, 3), (3, 4)}
        exp_cont_hops = {(4, 3), (3, 2), (4, 5), (5, 0)}
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert exp_req_hops == set(req_hops)
        assert exp_cont_hops == set(cont_hops)
        # At time 2 repeat request, expect cache hit
        hr.process_event(2, 0, 2, True)
        loc = self.view.content_locations(2)
        assert len(loc) == 2
        assert 2 in loc
        assert 4 in loc
        summary = self.collector.session_summary()
        exp_req_hops = {(0, 1), (1, 2)}
        exp_cont_hops = {(2, 1), (1, 0)}
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert exp_req_hops == set(req_hops)
        assert exp_cont_hops == set(cont_hops)
        # Now request from node 6, expect hit
        hr.process_event(3, 6, 2, True)
        loc = self.view.content_locations(2)
        assert len(loc) == 2
        assert 2 in loc
        assert 4 in loc
        summary = self.collector.session_summary()
        exp_req_hops = {(6, 2)}
        exp_cont_hops = {(2, 6)}
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert exp_req_hops == set(req_hops)
        assert exp_cont_hops == set(cont_hops)

    def test_hashrouting_hybrid_sm(self):
        hr = strategy.HashroutingHybridSM(self.view, self.controller)
        hr.authoritative_cache = lambda x: x
        # At time 1, receiver 0 requests content 2, expect asymmetric
        hr.process_event(1, 0, 3, True)
        loc = self.view.content_locations(3)
        assert len(loc) == 2
        assert 3 in loc
        assert 4 in loc
        summary = self.collector.session_summary()
        exp_req_hops = {(0, 1), (1, 2), (2, 3), (3, 4)}
        exp_cont_hops = {(4, 5), (5, 0), (4, 3)}
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert exp_req_hops == set(req_hops)
        assert exp_cont_hops == set(cont_hops)
        # At time 2, receiver 0 requests content 5, expect symm = mcast = asymm
        hr.process_event(2, 0, 5, True)
        loc = self.view.content_locations(5)
        assert len(loc) == 2
        assert 5 in loc
        assert 4 in loc
        summary = self.collector.session_summary()
        exp_req_hops = {(0, 5), (5, 4)}
        exp_cont_hops = {(4, 5), (5, 0)}
        req_hops = summary['request_hops']
        cont_hops = summary['content_hops']
        assert exp_req_hops == set(req_hops)
        assert exp_cont_hops == set(cont_hops)
