"""Implementations of all hash-routing strategies"""
from __future__ import division

import networkx as nx

from icarus.registry import register_strategy
from icarus.util import inheritdoc, multicast_tree, path_links
from icarus.scenarios.algorithms import extract_cluster_level_topology

from .base import Strategy


__all__ = [
       'Hashrouting',
       'HashroutingEdge',
       'HashroutingOnPath',
       'HashroutingClustered',
       'HashroutingSymmetric',
       'HashroutingAsymmetric',
       'HashroutingMulticast',
       'HashroutingHybridAM',
       'HashroutingHybridSM',
           ]


class BaseHashrouting(Strategy):
    """Base class for all hash-routing implementations."""

    @inheritdoc(Strategy)
    def __init__(self, view, controller, **kwargs):
        super(BaseHashrouting, self).__init__(view, controller)
        self.cache_nodes = view.cache_nodes()
        self.n_cache_nodes = len(self.cache_nodes)
        # Allocate results of hash function to caching nodes
        self.cache_assignment = {i: self.cache_nodes[i]
                                 for i in range(len(self.cache_nodes))}
        # Check if there are clusters
        if 'clusters' in self.view.topology().graph:
            self.clusters = self.view.topology().graph['clusters']
            # Convert to list in case it comes as set or iterable
            for i, cluster in enumerate(self.clusters):
                self.clusters[i] = list(cluster)
            self.cluster_size = {i: len(self.clusters[i])
                                 for i in range(len(self.clusters))}

    def authoritative_cache(self, content, cluster=None):
        """Return the authoritative cache node for the given content

        Parameters
        ----------
        content : any hashable type
            The identifier of the content
        cluster : int, optional
            If the topology is divided in clusters, then retun the authoritative
            cache responsible for the content in the specified cluster

        Returns
        -------
        authoritative_cache : any hashable type
            The node on which the authoritative cache is deployed
        """
        # TODO: I should probably consider using a better non-cryptographic hash
        # function, like xxhash
        h = hash(content)
        if cluster is not None:
            return self.clusters[cluster][h % self.cluster_size[cluster]]
        return self.cache_assignment[h % self.n_cache_nodes]

    def process_event(self, time, receiver, content, log):
        raise NotImplementedError('Cannot use BaseHashrouting class as is. '
                                  'This class is meant to be extended by other classes.')


@register_strategy('HASHROUTING')
class Hashrouting(BaseHashrouting):
    """Unified implementation of the three basic hash-routing schemes:
    symmetric, asymmetric and multicast.

    Hash-routing implementations are described in [1]_.

    According to these strategies, edge nodes receiving a content request
    compute a hash function mapping the content identifier to a specific caching
    node and forward the request to that specific node. If the cache holds the
    requested content, it is returned to the user, otherwise it is forwarded to
    the original source. Similarly, when a content is delivered to the
    requesting user, it can be cached only by the caching node associated to the
    content identifier by the hash function.

    References
    ----------
    .. [1] L. Saino, I. Psaras and G. Pavlou, Hash-routing Schemes for
           Information-Centric Networking, in Proceedings of ACM SIGCOMM ICN'13
           workshop. Available:
           https://lorenzosaino.github.io/publications/hashrouting-icn13.pdf
    .. [2] L. Saino, On the Design of Efficient Caching Systems, Ph.D. thesis
           University College London, Dec. 2015. Available:
           http://discovery.ucl.ac.uk/1473436/
    """

    def __init__(self, view, controller, routing, **kwargs):
        """Constructor

        Parameters
        ----------
        view : NetworkView
            An instance of the network view
        controller : NetworkController
            An instance of the network controller
        routing : str (SYMM | ASYMM | MULTICAST)
            Content routing option
        """
        super(Hashrouting, self).__init__(view, controller)
        self.routing = routing

    @inheritdoc(Strategy)
    def process_event(self, time, receiver, content, log):
        # get all required data
        source = self.view.content_source(content)
        cache = self.authoritative_cache(content)
        # handle (and log if required) actual request
        self.controller.start_session(time, receiver, content, log)
        # Forward request to authoritative cache
        self.controller.forward_request_path(receiver, cache)
        if self.controller.get_content(cache):
            # We have a cache hit here
            self.controller.forward_content_path(cache, receiver)
        else:
            # Cache miss: go all the way to source
            self.controller.forward_request_path(cache, source)
            if not self.controller.get_content(source):
                raise RuntimeError('The content is not found the expected source')
            if self.routing == 'SYMM':
                self.controller.forward_content_path(source, cache)
                # Insert in cache
                self.controller.put_content(cache)
                # Forward to receiver
                self.controller.forward_content_path(cache, receiver)
            elif self.routing == 'ASYMM':
                if cache in self.view.shortest_path(source, receiver):
                    # Forward to cache
                    self.controller.forward_content_path(source, cache)
                    # Insert in cache
                    self.controller.put_content(cache)
                    # Forward to receiver
                    self.controller.forward_content_path(cache, receiver)
                else:
                    # Forward to receiver straight away
                    self.controller.forward_content_path(source, receiver)
            elif self.routing == 'MULTICAST':
                if cache in self.view.shortest_path(source, receiver):
                    self.controller.forward_content_path(source, cache)
                    # Insert in cache
                    self.controller.put_content(cache)
                    # Forward to receiver
                    self.controller.forward_content_path(cache, receiver)
                else:
                    # Multicast
                    cache_path = self.view.shortest_path(source, cache)
                    recv_path = self.view.shortest_path(source, receiver)

                    # find what is the node that has to fork the content flow
                    for i in range(1, min([len(cache_path), len(recv_path)])):
                        if cache_path[i] != recv_path[i]:
                            fork_node = cache_path[i - 1]
                            break
                    else:
                        fork_node = cache
                    self.controller.forward_content_path(source, fork_node)
                    self.controller.forward_content_path(fork_node, receiver)
                    self.controller.forward_content_path(fork_node, cache,
                                                         main_path=False)
                self.controller.put_content(cache)
            else:
                raise ValueError("Routing %s not supported" % self.routing)
        self.controller.end_session()


@register_strategy('HR_EDGE_CACHE')
class HashroutingEdge(BaseHashrouting):
    """Hybrid hash-routing and edge caching.

    According to this strategy a fraction of the caching space in each cache is
    reserved for local caching. When a request is issued by a user, it is
    routed to the closes caching node and this caching node holds a copy of
    requested content in its local cache even if not authoritative for the
    requested content.

    Here we assume that each receiver is directly connected to one gateway,
    which is on the path to all other caches.

    References
    ----------
    .. [2] L. Saino, On the Design of Efficient Caching Systems, Ph.D. thesis
           University College London, Dec. 2015. Available:
           http://discovery.ucl.ac.uk/1473436/
    """

    def __init__(self, view, controller, routing, edge_cache_ratio, **kwargs):
        """Constructor

        Parameters
        ----------
        view : NetworkView
            An instance of the network view
        controller : NetworkController
            An instance of the network controller
        routing : str
            Content routing scheme: SYMM, ASYMM or MULTICAST
        edge_cache_ratio : float [0, 1]
            Ratio of cache allocated to uncoordinated edge cache
        """
        if edge_cache_ratio < 0 or edge_cache_ratio > 1:
            raise ValueError('edge_cache_ratio must be between 0 and 1')
        super(HashroutingEdge, self).__init__(view, controller)
        self.routing = routing
        self.controller.reserve_local_cache(edge_cache_ratio)
        self.proxy = {v: list(self.view.topology().adj[v].keys())[0]
                        for v in self.view.topology().receivers()}
        if any(v not in self.view.topology().cache_nodes() for v in self.proxy.values()):
            raise ValueError('There are receivers connected to a proxy without cache')

    @inheritdoc(Strategy)
    def process_event(self, time, receiver, content, log):
        # get all required data
        source = self.view.content_source(content)
        cache = self.authoritative_cache(content)
        # handle (and log if required) actual request
        self.controller.start_session(time, receiver, content, log)
        proxy = self.proxy[receiver]
        self.controller.forward_request_hop(receiver, proxy)
        if proxy != cache:
            if self.controller.get_content_local_cache(proxy):
                self.controller.forward_content_hop(proxy, receiver)
                self.controller.end_session()
                return
            else:
                # Forward request to authoritative cache
                self.controller.forward_request_path(proxy, cache)
        if self.controller.get_content(cache):
            # We have a cache hit here
            self.controller.forward_content_path(cache, proxy)
        else:
            # Cache miss: go all the way to source
            self.controller.forward_request_path(cache, source)
            if not self.controller.get_content(source):
                raise RuntimeError('The content is not found the expected source')
            if self.routing == 'SYMM':
                self.controller.forward_content_path(source, cache)
                # Insert in cache
                self.controller.put_content(cache)
                # Forward to receiver
                self.controller.forward_content_path(cache, proxy)
            elif self.routing == 'ASYMM':
                if cache in self.view.shortest_path(source, proxy):
                    # Forward to cache
                    self.controller.forward_content_path(source, cache)
                    # Insert in cache
                    self.controller.put_content(cache)
                    # Forward to receiver
                    self.controller.forward_content_path(cache, proxy)
                else:
                    # Forward to receiver straight away
                    self.controller.forward_content_path(source, proxy)
            elif self.routing == 'MULTICAST':
                if cache in self.view.shortest_path(source, proxy):
                    self.controller.forward_content_path(source, cache)
                    # Insert in cache
                    self.controller.put_content(cache)
                    # Forward to receiver
                    self.controller.forward_content_path(cache, receiver)
                else:
                    # Multicast
                    cache_path = self.view.shortest_path(source, cache)
                    recv_path = self.view.shortest_path(source, proxy)

                    # find what is the node that has to fork the content flow
                    for i in range(1, min([len(cache_path), len(recv_path)])):
                        if cache_path[i] != recv_path[i]:
                            fork_node = cache_path[i - 1]
                            break
                    else: fork_node = cache
                    self.controller.forward_content_path(source, fork_node)
                    self.controller.forward_content_path(fork_node, proxy)
                    self.controller.forward_content_path(fork_node, cache, main_path=False)
                self.controller.put_content(cache)
            else:
                raise ValueError("Routing %s not recognized" % self.routing)

        if proxy != cache:
            self.controller.put_content_local_cache(proxy)
        self.controller.forward_content_hop(proxy, receiver)
        self.controller.end_session()


@register_strategy('HR_ON_PATH')
class HashroutingOnPath(BaseHashrouting):
    """Hybrid hash-routing and on-path caching.

    This strategy differs from HashroutingEdge for the fact that in
    HashroutingEdge, the local fraction of the cache is queried only by traffic
    of endpoints directly attached to the caching node. In HashroutingOnPath
    the local cache is queried by all traffic being forwarded by the node.

    References
    ----------
    .. [2] L. Saino, On the Design of Efficient Caching Systems, Ph.D. thesis
           University College London, Dec. 2015. Available:
           http://discovery.ucl.ac.uk/1473436/
    """

    def __init__(self, view, controller, routing, on_path_cache_ratio, **kwargs):
        """Constructor

        Parameters
        ----------
        view : NetworkView
            An instance of the network view
        controller : NetworkController
            An instance of the network controller
        routing : str
            Content routing scheme: SYMM, ASYMM or MULTICAST
        on_path_cache_ratio : float [0, 1]
            Ratio of cache allocated to uncoordinated on-path cache
        """
        if on_path_cache_ratio < 0 or on_path_cache_ratio > 1:
            raise ValueError('on_path_cache_ratio must be between 0 and 1')
        super(HashroutingOnPath, self).__init__(view, controller)
        self.routing = routing
        self.controller.reserve_local_cache(on_path_cache_ratio)

    @inheritdoc(Strategy)
    def process_event(self, time, receiver, content, log):
        # get all required data
        source = self.view.content_source(content)
        cache = self.authoritative_cache(content)
        # handle (and log if required) actual request
        self.controller.start_session(time, receiver, content, log)
        # Forward request to authoritative cache and check all local caches on path
        path = self.view.shortest_path(receiver, cache)
        for u, v in path_links(path):
            self.controller.forward_request_hop(u, v)
            if v != cache:
                if self.controller.get_content_local_cache(v):
                    serving_node = v
                    direct_return = True
                    break
        else:
            # No cache hits from local caches on path, query authoritative cache
            if self.controller.get_content(cache):
                serving_node = v
                direct_return = True
            else:
                path = self.view.shortest_path(cache, source)
                for u, v in path_links(path):
                    self.controller.forward_request_hop(u, v)
                    if v != source:
                        if self.controller.get_content_local_cache(v):
                            serving_node = v
                            direct_return = False
                            break
                else:
                    # No hits from local caches in cache -> source path
                    # Get content from the source
                    self.controller.get_content(source)
                    serving_node = source
                    direct_return = False
        # Now we have a serving node, let's return the content, while storing
        # it on all opportunistic caches on the path
        if direct_return:
            # Here I just need to return the content directly to the user
            path = list(reversed(self.view.shortest_path(receiver, serving_node)))
            for u, v in path_links(path):
                self.controller.forward_content_hop(u, v)
                if v != receiver:
                    self.controller.put_content_local_cache(v)
            self.controller.end_session()
            return
        # Here I need to see whether I need symm, asymm or multicast delivery
        if self.routing == 'SYMM':
            links = path_links(list(reversed(self.view.shortest_path(cache, serving_node)))) + \
                   path_links(list(reversed(self.view.shortest_path(receiver, cache))))
            for u, v in links:
                self.controller.forward_content_hop(u, v)
                if v == cache:
                    self.controller.put_content(v)
                else:
                    self.controller.put_content_local_cache(v)
        elif self.routing == 'ASYMM':
            path = list(reversed(self.view.shortest_path(receiver, serving_node)))
            for u, v in path_links(path):
                self.controller.forward_content_hop(u, v)
                if v == cache:
                    self.controller.put_content(v)
                else:
                    self.controller.put_content_local_cache(v)
        elif self.routing == 'MULTICAST':
            main_path = set(path_links(self.view.shortest_path(serving_node, receiver)))
            mcast_tree = multicast_tree(self.view.all_pairs_shortest_paths(),
                                        serving_node, [receiver, cache])
            cache_branch = mcast_tree.difference(main_path)
            for u, v in cache_branch:
                self.controller.forward_content_hop(u, v, main_path=False)
                if v == cache:
                    self.controller.put_content(v)
                else:
                    self.controller.put_content_local_cache(v)
            for u, v in main_path:
                self.controller.forward_content_hop(u, v, main_path=True)
                if v == cache:
                    self.controller.put_content(v)
                else:
                    self.controller.put_content_local_cache(v)
        else:
            raise ValueError("Routing %s not supported" % self.routing)
        self.controller.end_session()


@register_strategy('HR_CLUSTER')
class HashroutingClustered(BaseHashrouting):
    """Hash-routing with clustering of the network.

    According to ths strategy, nodes of the network are divided in a number of
    clusters and hash-routing is used withing each of this clusters. In case of
    cache miss at a cluster, requests are forwarded to other clusters on the
    path to the original source.

    References
    ----------
    .. [2] L. Saino, On the Design of Efficient Caching Systems, Ph.D. thesis
           University College London, Dec. 2015. Available:
           http://discovery.ucl.ac.uk/1473436/
    """

    def __init__(self, view, controller, intra_routing, inter_routing='LCE', **kwargs):
        """Constructor

        Parameters
        ----------
        view : NetworkView
            An instance of the network view
        controller : NetworkController
            An instance of the network controller
        intra_routing : str
            Intra-cluster content routing scheme: SYMM, ASYMM or MULTICAST
        inter_routing : str
            Inter-cluster content routing scheme. Only supported LCE
        """
        super(HashroutingClustered, self).__init__(view, controller)
        if intra_routing not in ('SYMM', 'ASYMM', 'MULTICAST'):
            raise ValueError('Intra-cluster routing policy %s not supported'
                             % intra_routing)
        self.intra_routing = intra_routing
        self.inter_routing = inter_routing
        self.cluster_topology = extract_cluster_level_topology(view.topology())
        self.cluster_sp = dict(nx.all_pairs_shortest_path(self.cluster_topology))

    @inheritdoc(Strategy)
    def process_event(self, time, receiver, content, log):
        # get all required data
        source = self.view.content_source(content)
        # handle (and log if required) actual request
        self.controller.start_session(time, receiver, content, log)

        receiver_cluster = self.view.cluster(receiver)
        source_cluster = self.view.cluster(source)
        cluster_path = self.cluster_sp[receiver_cluster][source_cluster]

        if self.inter_routing == 'LCE':
            start = receiver
            for cluster in cluster_path:
                cache = self.authoritative_cache(content, cluster)
                # Forward request to authoritative cache
                self.controller.forward_request_path(start, cache)
                start = cache
                if self.controller.get_content(cache):
                    break
            else:
                # Loop was never broken, cache miss
                self.controller.forward_request_path(start, source)
                start = source
                if not self.controller.get_content(source):
                    raise RuntimeError('The content is not found the expected source')
        elif self.inter_routing == 'EDGE':
            cache = self.authoritative_cache(content, receiver_cluster)
            self.controller.forward_request_path(receiver, cache)
            if self.controller.get_content(cache):
                self.controller.forward_content_path(cache, receiver)
                self.controller.end_session()
                return
            else:
                self.controller.forward_request_path(cache, source)
                self.controller.get_content(source)
                cluster = source_cluster
                start = source

        # Now "start" is the node that is serving the content
        cluster_path = list(reversed(self.cluster_sp[receiver_cluster][cluster]))
        if self.inter_routing == 'LCE':
            if self.intra_routing == 'SYMM':
                for cluster in cluster_path:
                    cache = self.authoritative_cache(content, cluster)
                    # Forward request to authoritative cache
                    self.controller.forward_content_path(start, cache)
                    self.controller.put_content(cache)
                    start = cache
                self.controller.forward_content_path(start, receiver)
            elif self.intra_routing == 'ASYMM':
                self.controller.forward_content_path(start, receiver)
                path = self.view.shortest_path(start, receiver)
                traversed_clusters = set(self.view.cluster(v) for v in path)
                authoritative_caches = set(self.authoritative_cache(content, cluster)
                                        for cluster in traversed_clusters)
                traversed_caches = authoritative_caches.intersection(set(path))
                for v in traversed_caches:
                    self.controller.put_content(v)
            elif self.intra_routing == 'MULTICAST':
                destinations = [self.authoritative_cache(content, cluster)
                                for cluster in cluster_path]
                for v in destinations:
                    self.controller.put_content(v)
                main_path = set(path_links(self.view.shortest_path(start, receiver)))
                mcast_tree = multicast_tree(self.view.all_pairs_shortest_paths(), start, destinations)
                mcast_tree = mcast_tree.difference(main_path)
                for u, v in mcast_tree:
                    self.controller.forward_content_hop(u, v, main_path=False)
                for u, v in main_path:
                    self.controller.forward_content_hop(u, v, main_path=True)
            else:
                raise ValueError("Intra-cluster routing %s not supported" % self.intra_routing)
        elif self.inter_routing == 'EDGE':
            if self.intra_routing == 'SYMM':
                cache = self.authoritative_cache(content, cluster_path[-1])
                self.controller.forward_content_path(start, cache)
                self.controller.forward_content_path(cache, receiver)
                path = self.view.shortest_path(start, receiver)
                traversed_clusters = set(self.view.cluster(v) for v in path)
                authoritative_caches = set(self.authoritative_cache(content, cluster)
                                        for cluster in traversed_clusters)
                traversed_caches = authoritative_caches.intersection(set(path))
                for v in traversed_caches:
                    self.controller.put_content(v)
                if cache not in traversed_caches:
                    self.controller.put_content(cache)
            elif self.intra_routing == 'ASYMM':
                self.controller.forward_content_path(start, receiver)
                path = self.view.shortest_path(start, receiver)
                traversed_clusters = set(self.view.cluster(v) for v in path)
                authoritative_caches = set(self.authoritative_cache(content, cluster)
                                        for cluster in traversed_clusters)
                traversed_caches = authoritative_caches.intersection(set(path))
                for v in traversed_caches:
                    self.controller.put_content(v)
            elif self.intra_routing == 'MULTICAST':
                cache = self.authoritative_cache(content, cluster_path[-1])
                self.controller.put_content(cache)
                main_path = set(path_links(self.view.shortest_path(start, receiver)))
                mcast_tree = multicast_tree(self.view.all_pairs_shortest_paths(), start, [cache])
                mcast_tree = mcast_tree.difference(main_path)
                for u, v in mcast_tree:
                    self.controller.forward_content_hop(u, v, main_path=False)
                for u, v in main_path:
                    self.controller.forward_content_hop(u, v, main_path=True)
        else:
            raise ValueError("Inter-cluster routing %s not supported" % self.inter_routing)
        self.controller.end_session()


@register_strategy('HR_SYMM')
class HashroutingSymmetric(Hashrouting):
    """Hash-routing with symmetric routing (HR SYMM)

    According to this strategy, each content is routed following the same path
    of the request.

    References
    ----------
    .. [1] L. Saino, I. Psaras and G. Pavlou, Hash-routing Schemes for
           Information-Centric Networking, in Proceedings of ACM SIGCOMM ICN'13
           workshop. Available:
           https://lorenzosaino.github.io/publications/hashrouting-icn13.pdf
    .. [2] L. Saino, On the Design of Efficient Caching Systems, Ph.D. thesis
           University College London, Dec. 2015. Available:
           http://discovery.ucl.ac.uk/1473436/
    """

    @inheritdoc(Strategy)
    def __init__(self, view, controller, **kwargs):
        super(HashroutingSymmetric, self).__init__(view, controller, 'SYMM', **kwargs)


@register_strategy('HR_ASYMM')
class HashroutingAsymmetric(Hashrouting):
    """Hash-routing with asymmetric routing (HR ASYMM)

    According to this strategy, each content fetched from an original source,
    as a result of a cache miss, is routed towards the receiver following the
    shortest path. If the authoritative cache is on the path, then it caches
    the content, otherwise not.

    References
    ----------
    .. [1] L. Saino, I. Psaras and G. Pavlou, Hash-routing Schemes for
           Information-Centric Networking, in Proceedings of ACM SIGCOMM ICN'13
           workshop. Available:
           https://lorenzosaino.github.io/publications/hashrouting-icn13.pdf
    .. [2] L. Saino, On the Design of Efficient Caching Systems, Ph.D. thesis
           University College London, Dec. 2015. Available:
           http://discovery.ucl.ac.uk/1473436/
    """

    @inheritdoc(Strategy)
    def __init__(self, view, controller, **kwargs):
        super(HashroutingAsymmetric, self).__init__(view, controller, 'ASYMM', **kwargs)


@register_strategy('HR_MULTICAST')
class HashroutingMulticast(Hashrouting):
    """Hash-routing implementation with multicast delivery of content packets.

    In this strategy, if there is a cache miss, when contents return in
    the domain, they are multicast. One copy is sent to the authoritative cache
    and the other to the receiver. If the cache is on the path from source to
    receiver, this strategy behaves as a normal symmetric hash-routing
    strategy.

    References
    ----------
    .. [1] L. Saino, I. Psaras and G. Pavlou, Hash-routing Schemes for
           Information-Centric Networking, in Proceedings of ACM SIGCOMM ICN'13
           workshop. Available:
           https://lorenzosaino.github.io/publications/hashrouting-icn13.pdf
    .. [2] L. Saino, On the Design of Efficient Caching Systems, Ph.D. thesis
           University College London, Dec. 2015. Available:
           http://discovery.ucl.ac.uk/1473436/
    """

    @inheritdoc(Strategy)
    def __init__(self, view, controller, **kwargs):
        super(HashroutingMulticast, self).__init__(view, controller, 'MULTICAST', **kwargs)


@register_strategy('HR_HYBRID_AM')
class HashroutingHybridAM(BaseHashrouting):
    """Hash-routing implementation with hybrid asymmetric-multicast delivery of
    content packets.

    In this strategy, if there is a cache miss, when content packets return in
    the domain, the packet is delivered to the receiver following the shortest
    path. If the additional number of hops required to send a copy to the
    authoritative cache is below a specific fraction of the network diameter,
    then one copy is sent to the authoritative cache as well. If the cache is
    on the path from source to receiver, this strategy behaves as a normal
    symmetric hash-routing strategy.

    References
    ----------
    .. [1] L. Saino, I. Psaras and G. Pavlou, Hash-routing Schemes for
           Information-Centric Networking, in Proceedings of ACM SIGCOMM ICN'13
           workshop. Available:
           https://lorenzosaino.github.io/publications/hashrouting-icn13.pdf
    """

    def __init__(self, view, controller, max_stretch=0.2, **kwargs):
        """Constructor

        Parameters
        ----------
        view : NetworkView
            An instance of the network view
        controller : NetworkController
            An instance of the network controller
        max_stretch : float, optional
            The threshold path stretch (normalized by network diameter) set
            to decide whether using asymmetric or multicast routing. If the
            path stretch required to deliver a content is above max_stretch
            asymmetric delivery is used, otherwise multicast delivery is used.
        """
        super(HashroutingHybridAM, self).__init__(view, controller)
        self.max_stretch = nx.diameter(view.topology()) * max_stretch

    @inheritdoc(Strategy)
    def process_event(self, time, receiver, content, log):
        # get all required data
        source = self.view.content_source(content)
        cache = self.authoritative_cache(content)
        # handle (and log if required) actual request
        self.controller.start_session(time, receiver, content, log)
        # Forward request to authoritative cache
        self.controller.forward_request_path(receiver, cache)
        if self.controller.get_content(cache):
            # We have a cache hit here
            self.controller.forward_content_path(cache, receiver)
        else:
            # Cache miss: go all the way to source
            self.controller.forward_request_path(cache, source)
            if not self.controller.get_content(source):
                raise RuntimeError('The content was not found at the expected source')

            if cache in self.view.shortest_path(source, receiver):
                # Forward to cache
                self.controller.forward_content_path(source, cache)
                # Insert in cache
                self.controller.put_content(cache)
                # Forward to receiver
                self.controller.forward_content_path(cache, receiver)
            else:
                # Multicast
                cache_path = self.view.shortest_path(source, cache)
                recv_path = self.view.shortest_path(source, receiver)

                # find what is the node that has to fork the content flow
                for i in range(1, min([len(cache_path), len(recv_path)])):
                    if cache_path[i] != recv_path[i]:
                        fork_node = cache_path[i - 1]
                        break
                else:
                    fork_node = cache
                self.controller.forward_content_path(source, receiver, main_path=True)
                # multicast to cache only if stretch is under threshold
                if len(self.view.shortest_path(fork_node, cache)) - 1 < self.max_stretch:
                    self.controller.forward_content_path(fork_node, cache, main_path=False)
                    self.controller.put_content(cache)
        self.controller.end_session()


@register_strategy('HR_HYBRID_SM')
class HashroutingHybridSM(BaseHashrouting):
    """Hash-routing implementation with hybrid symmetric-multicast delivery of
    content packets.

    In this implementation, the edge router receiving a content packet decides
    whether to deliver the packet using multicast or symmetric hash-routing
    based on the total cost for delivering the Data to both cache and receiver
    in terms of hops.

    References
    ----------
    .. [1] L. Saino, I. Psaras and G. Pavlou, Hash-routing Schemes for
           Information-Centric Networking, in Proceedings of ACM SIGCOMM ICN'13
           workshop. Available:
           https://lorenzosaino.github.io/publications/hashrouting-icn13.pdf
    """

    @inheritdoc(Strategy)
    def __init__(self, view, controller, **kwargs):
        super(HashroutingHybridSM, self).__init__(view, controller)

    @inheritdoc(Strategy)
    def process_event(self, time, receiver, content, log):
        # get all required data
        source = self.view.content_source(content)
        cache = self.authoritative_cache(content)
        # handle (and log if required) actual request
        self.controller.start_session(time, receiver, content, log)
        # Forward request to authoritative cache
        self.controller.forward_request_path(receiver, cache)
        if self.controller.get_content(cache):
            # We have a cache hit here
            self.controller.forward_content_path(cache, receiver)
        else:
            # Cache miss: go all the way to source
            self.controller.forward_request_path(cache, source)
            if not self.controller.get_content(source):
                raise RuntimeError('The content is not found the expected source')

            if cache in self.view.shortest_path(source, receiver):
                self.controller.forward_content_path(source, cache)
                # Insert in cache
                self.controller.put_content(cache)
                # Forward to receiver
                self.controller.forward_content_path(cache, receiver)
            else:
                # Multicast
                cache_path = self.view.shortest_path(source, cache)
                recv_path = self.view.shortest_path(source, receiver)

                # find what is the node that has to fork the content flow
                for i in range(1, min([len(cache_path), len(recv_path)])):
                    if cache_path[i] != recv_path[i]:
                        fork_node = cache_path[i - 1]
                        break
                else:
                    fork_node = cache

                symmetric_path_len = len(self.view.shortest_path(source, cache)) + \
                                     len(self.view.shortest_path(cache, receiver)) - 2
                multicast_path_len = len(self.view.shortest_path(source, fork_node)) + \
                                     len(self.view.shortest_path(fork_node, cache)) + \
                                     len(self.view.shortest_path(fork_node, receiver)) - 3

                self.controller.put_content(cache)
                # If symmetric and multicast have equal cost, choose symmetric
                # because of easier packet processing
                if symmetric_path_len <= multicast_path_len:  # use symmetric delivery
                    # Symmetric delivery
                    self.controller.forward_content_path(source, cache, main_path=True)
                    self.controller.forward_content_path(cache, receiver, main_path=True)
                else:
                    # Multicast delivery
                    self.controller.forward_content_path(source, receiver, main_path=True)
                    self.controller.forward_content_path(fork_node, cache, main_path=False)
                self.controller.end_session()
