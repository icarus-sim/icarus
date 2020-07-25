from __future__ import division

import icarus.execution as collectors


class TestLinkLoadCollector(object):

    def test_internal_external_custom_size(self):

        req_size = 500
        cont_size = 700

        link_type = {(1, 2): 'internal', (2, 3): 'external',
                     (2, 1): 'internal', (3, 2): 'external'}

        view = type('MockNetworkView', (), {'link_type': lambda s, u, v: link_type[(u, v)]})()

        c = collectors.LinkLoadCollector(view, req_size=req_size, content_size=cont_size)

        c.start_session(3.0, 1, 4)
        c.request_hop(1, 2)
        c.content_hop(2, 1)
        c.end_session()

        c.start_session(5.0, 1, 4)
        c.request_hop(1, 2)
        c.request_hop(2, 3)
        c.content_hop(3, 2)
        c.content_hop(2, 1)
        c.end_session()

        res = c.results()

        int_load = res['PER_LINK_INTERNAL']
        ext_load = res['PER_LINK_EXTERNAL']
        assert 2 * req_size / 2 == int_load[(1, 2)]
        assert 2 * cont_size / 2 == int_load[(2, 1)]
        assert req_size / 2 == ext_load[(2, 3)]
        assert cont_size / 2 == ext_load[(3, 2)]
        mean_int = res['MEAN_INTERNAL']
        mean_ext = res['MEAN_EXTERNAL']
        assert (req_size + cont_size) / 2 == mean_int
        assert (req_size + cont_size) / 4 == mean_ext

    def test_internal_links_only(self):

        req_size = 500
        cont_size = 700

        link_type = {(1, 2): 'internal', (2, 3): 'internal',
                     (2, 1): 'internal', (3, 2): 'internal'}

        view = type('MockNetworkView', (), {'link_type': lambda s, u, v: link_type[(u, v)]})()

        c = collectors.LinkLoadCollector(view, req_size=req_size, content_size=cont_size)

        c.start_session(3.0, 1, 4)
        c.request_hop(1, 2)
        c.content_hop(2, 1)
        c.end_session()

        c.start_session(5.0, 1, 4)
        c.request_hop(1, 2)
        c.request_hop(2, 3)
        c.content_hop(3, 2)
        c.content_hop(2, 1)
        c.end_session()

        res = c.results()
        mean_ext = res['MEAN_EXTERNAL']
        ext_load = res['PER_LINK_EXTERNAL']
        assert 0 == mean_ext
        assert 0 == len(ext_load)

    def test_external_links_only(self):

        req_size = 500
        cont_size = 700

        link_type = {(1, 2): 'external', (2, 3): 'external',
                     (2, 1): 'external', (3, 2): 'external'}

        view = type('MockNetworkView', (), {'link_type': lambda s, u, v: link_type[(u, v)]})()

        c = collectors.LinkLoadCollector(view, req_size=req_size, content_size=cont_size)

        c.start_session(3.0, 1, 'CONTENT')
        c.request_hop(1, 2)
        c.content_hop(2, 1)
        c.end_session()

        c.start_session(5.0, 1, 'CONTENT')
        c.request_hop(1, 2)
        c.request_hop(2, 3)
        c.content_hop(3, 2)
        c.content_hop(2, 1)
        c.end_session()

        res = c.results()
        mean_ext = res['MEAN_INTERNAL']
        ext_load = res['PER_LINK_INTERNAL']
        assert 0 == mean_ext
        assert 0 == len(ext_load)


class TestLatencyCollector(object):

    def test_base(self):

        link_delay = {(1, 2): 2, (2, 3): 10,
                      (2, 1): 4, (3, 2): 20}
        view = type('MockNetworkView', (), {'link_delay': lambda s, u, v: link_delay[(u, v)]})()

        c = collectors.LatencyCollector(view)

        c.start_session(3.0, 1, 'CONTENT')
        c.request_hop(1, 2)
        c.content_hop(2, 1)
        c.end_session()

        c.start_session(5.0, 1, 'CONTENT')
        c.request_hop(1, 2)
        c.request_hop(2, 3)
        c.content_hop(3, 2)
        c.content_hop(2, 1)
        c.end_session()

        res = c.results()
        assert (10 + 20 + 2 * (2 + 4)) / 2 == res['MEAN']

    def test_main_path(self):

        link_delay = {(1, 2): 2, (2, 3): 10,
                      (2, 1): 4, (3, 2): 20}
        view = type('MockNetworkView', (), {'link_delay': lambda s, u, v: link_delay[(u, v)]})()

        c = collectors.LatencyCollector(view)

        c.start_session(3.0, 1, 'CONTENT')
        c.request_hop(1, 2)
        c.content_hop(2, 1)
        c.end_session()

        c.start_session(5.0, 1, 'CONTENT')
        c.request_hop(1, 2)
        c.request_hop(2, 3)
        c.request_hop(2, 1, main_path=False)
        c.content_hop(3, 2)
        c.content_hop(2, 1)
        c.content_hop(2, 3, main_path=False)
        c.end_session()

        res = c.results()
        assert (10 + 20 + 2 * (2 + 4)) / 2 == res['MEAN']


class TestCacheHitRatioCollector(object):

    def test_base(self):

        view = type('MockNetworkView', (), {})()

        c = collectors.CacheHitRatioCollector(view)

        c.start_session(3.0, 1, 'CONTENT')
        c.cache_hit(1)
        c.end_session()

        c.start_session(4.0, 1, 'CONTENT')
        c.server_hit(2)
        c.end_session()

        res = c.results()
        assert 0.5 == res['MEAN']

    def test_per_node(self):

        view = type('MockNetworkView', (), {})()

        c = collectors.CacheHitRatioCollector(view, per_node=True)

        c.start_session(3.0, 1, 'CONTENT')
        c.cache_hit(1)
        c.end_session()

        c.start_session(4.0, 1, 'CONTENT')
        c.cache_hit(1)
        c.end_session()

        c.start_session(5.0, 1, 'CONTENT')
        c.cache_hit(2)
        c.end_session()

        c.start_session(6.0, 1, 'CONTENT')
        c.cache_hit(3)
        c.end_session()

        c.start_session(7.0, 1, 'CONTENT')
        c.server_hit(4)
        c.end_session()

        res = c.results()
        assert {1: 0.4, 2: 0.2, 3: 0.2} == res['PER_NODE_CACHE_HIT_RATIO']
        assert {4: 0.2} == res['PER_NODE_SERVER_HIT_RATIO']

    def test_per_content(self):

        view = type('MockNetworkView', (), {})()

        c = collectors.CacheHitRatioCollector(view, content_hits=True)

        c.start_session(3.0, 'RECV', 1)
        c.cache_hit(1)
        c.end_session()

        c.start_session(4.0, 'RECV', 1)
        c.server_hit(2)
        c.end_session()

        c.start_session(5.0, 'RECV', 2)
        c.cache_hit(3)
        c.end_session()

        c.start_session(6.0, 'RECV', 2)
        c.server_hit(4)
        c.end_session()

        c.start_session(7.0, 'RECV', 2)
        c.server_hit(5)
        c.end_session()

        c.start_session(8.0, 'RECV', 2)
        c.server_hit(5)
        c.end_session()

        res = c.results()
        assert {1: 0.5, 2: 0.25} == res['PER_CONTENT']
