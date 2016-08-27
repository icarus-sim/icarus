from __future__ import division
import sys
if sys.version_info[:2] >= (2, 7):
    import unittest
else:
    try:
        import unittest2 as unittest
    except ImportError:
        raise ImportError("The unittest2 package is needed to run the tests.")
del sys

import icarus.execution as collectors


class TestLinkLoadCollector(unittest.TestCase):

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
        self.assertEqual(2 * req_size / 2, int_load[(1, 2)])
        self.assertEqual(2 * cont_size / 2, int_load[(2, 1)])
        self.assertEqual(req_size / 2, ext_load[(2, 3)])
        self.assertEqual(cont_size / 2, ext_load[(3, 2)])
        mean_int = res['MEAN_INTERNAL']
        mean_ext = res['MEAN_EXTERNAL']
        self.assertEqual((req_size + cont_size) / 2, mean_int)
        self.assertEqual((req_size + cont_size) / 4, mean_ext)

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
        self.assertEqual(0, mean_ext)
        self.assertEqual(0, len(ext_load))

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
        self.assertEqual(0, mean_ext)
        self.assertEqual(0, len(ext_load))


class TestLatencyCollector(unittest.TestCase):

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
        self.assertEqual((10 + 20 + 2 * (2 + 4)) / 2, res['MEAN'])

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
        self.assertEqual((10 + 20 + 2 * (2 + 4)) / 2, res['MEAN'])

