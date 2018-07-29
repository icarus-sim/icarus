"""Implementations of all off-path strategies"""
from __future__ import division

import networkx as nx

from icarus.registry import register_strategy
from icarus.util import inheritdoc, path_links

from .base import Strategy

__all__ = [
       'NearestReplicaRouting'
           ]


@register_strategy('NRR')
class NearestReplicaRouting(Strategy):
    """Ideal Nearest Replica Routing (NRR) strategy.

    In this strategy, a request is forwarded to the topologically closest node
    holding a copy of the requested item. This strategy is ideal, as it is
    implemented assuming that each node knows the nearest replica of a content
    without any signaling

    On the return path, content can be caching according to a variety of
    metacaching policies. LCE and LCD are currently supported.
    """

    def __init__(self, view, controller, metacaching, implementation='ideal',
                 radius=4, **kwargs):
        """Constructor

        Parameters
        ----------
        view : NetworkView
            An instance of the network view
        controller : NetworkController
            An instance of the network controller
        metacaching : str (LCE | LCD)
            Metacaching policy used
        implementation : str, optional
            The implementation of the nearest replica discovery. Currently on
            ideal routing is implemented, in which each node has omniscient
            knowledge of the location of each content.
        radius : int, optional
            Radius used by nodes to discover the location of a content. Not
            used by ideal routing.
        """
        super(NearestReplicaRouting, self).__init__(view, controller)
        if metacaching not in ('LCE', 'LCD'):
            raise ValueError("Metacaching policy %s not supported" % metacaching)
        if implementation not in ('ideal', 'approx_1', 'approx_2'):
            raise ValueError("Implementation %s not supported" % implementation)
        self.metacaching = metacaching
        self.implementation = implementation
        self.radius = radius
        self.distance = dict(nx.all_pairs_dijkstra_path_length(self.view.topology(),
                                                               weight='delay'))

    @inheritdoc(Strategy)
    def process_event(self, time, receiver, content, log):
        # get all required data
        locations = self.view.content_locations(content)
        nearest_replica = min(locations, key=lambda x: self.distance[receiver][x])
        # Route request to nearest replica
        self.controller.start_session(time, receiver, content, log)
        if self.implementation == 'ideal':
            self.controller.forward_request_path(receiver, nearest_replica)
        elif self.implementation == 'approx_1':
            # Floods actual request packets
            paths = {loc: len(self.view.shortest_path(receiver, loc)[:self.radius])
                     for loc in locations}
            # TODO: Continue
            raise NotImplementedError("Not implemented")
        elif self.implementation == 'approx_2':
            # Floods meta-request packets
            # TODO: Continue
            raise NotImplementedError("Not implemented")
        else:
            # Should never reach this block anyway
            raise ValueError("Implementation %s not supported"
                             % str(self.implementation))
        self.controller.get_content(nearest_replica)
        # Now we need to return packet and we have options
        path = list(reversed(self.view.shortest_path(receiver, nearest_replica)))
        if self.metacaching == 'LCE':
            for u, v in path_links(path):
                self.controller.forward_content_hop(u, v)
                if self.view.has_cache(v) and not self.view.cache_lookup(v, content):
                    self.controller.put_content(v)
        elif self.metacaching == 'LCD':
            copied = False
            for u, v in path_links(path):
                self.controller.forward_content_hop(u, v)
                if not copied and v != receiver and self.view.has_cache(v):
                    self.controller.put_content(v)
                    copied = True
        else:
            raise ValueError('Metacaching policy %s not supported'
                             % self.metacaching)
        self.controller.end_session()
