"""Various algorithms used for optimal cache placement."""
import random

import numpy as np
import networkx as nx

import fnss

from icarus.util import path_links


__all__ = [
    'pam',
    'extract_cluster_level_topology',
    'deploy_clusters',
    'compute_clusters',
    'compute_p_median',
           ]


def pam(distances, k, n_iter=10):
    """Compute k-medoids using the PAM algorithm

    Parameters
    ----------
    distances : 2-d NumPy array
        Array of distances between points
    k : int
        Number of clusters
    n_iter : int
        Number of iterations to repeat. Each repetition is executed using a
        different initial random assignment. Repetiting the experiment allow
        to reach different local optima, possibly achieving a best solution.

    Return
    ------
    clusters : 1-d NumPy array
        Array mapping point to medoid, e.g. if point i is mapped to medoid j
        then clusters[i] = j
    medoids : 1-d NumPy array
        Array listing (in no particular order) all medoids
    cost : float
        Cost of the solution

    Notes
    -----
    Implementation based on:
    https://github.com/salspaugh/machine_learning/blob/master/clustering/kmedoids.py
    """
    def assign_points_to_clusters(medoids, distances):
        """Return a 1-d array having for at each index the medoid the element
        belongs to.

        E.g. if point i is mapped to medoid j, clusters[i] = j
        """
        distances_to_medoids = distances[:, medoids]
        clusters = medoids[np.argmin(distances_to_medoids, axis=1)]
        clusters[medoids] = medoids
        return clusters

    def compute_new_medoid(cluster, distances):
        mask = np.ones(distances.shape)
        mask[np.ix_(cluster, cluster)] = 0.
        cluster_distances = np.ma.masked_array(data=distances, mask=mask, fill_value=10e9)
        costs = cluster_distances.sum(axis=1)
        return costs.argmin(axis=0, fill_value=np.inf)

    def clusters(distances, k):
        m = distances.shape[0]  # number of points
        if k > m:
            raise ValueError("k is greater than the number of points")

        if hasattr(np.random, 'choice'):
            curr_medoids = np.random.choice(np.arange(m, dtype=int), k, replace=False)
        else:
            # This is only if I use NumPy < 1.7
            curr_medoids = np.asarray(random.sample(np.arange(m, dtype=int), k))

        old_medoids = np.empty(k)
        new_medoids = np.empty(k)

        # Set a negative value to ensure execution of while loop
        old_medoids[0] = -1

        # Until the medoids stop updating, do the following:
        while not np.all(old_medoids == curr_medoids):
            # Assign each point to cluster with closest medoid
            clusters = assign_points_to_clusters(curr_medoids, distances)

            # Update cluster medoids to be lowest cost point.
            for curr_medoid in curr_medoids:
                cluster = np.where(clusters == curr_medoid)[0]
                new_medoids[curr_medoids == curr_medoid] = compute_new_medoid(cluster, distances)

            old_medoids[:] = curr_medoids[:]
            curr_medoids[:] = new_medoids[:]
            cost = np.sum(distances[np.arange(m), clusters])
        return clusters, curr_medoids, cost

    min_cost = np.inf
    opt_clusters = None
    opt_medoids = None

    for _ in range(n_iter):
        curr_clusters, curr_medoids, curr_cost = clusters(distances, k)
        if curr_cost < min_cost:
            min_cost = curr_cost
            opt_clusters = curr_clusters
            opt_medoids = curr_medoids
    return opt_clusters, opt_medoids, min_cost


def extract_cluster_level_topology(topology):
    """Build a cluster-level topology.

    Each node in the topology must be have the 'cluster' attribute

    Parameters
    ----------
    topology : Topology
        The router-level topology

    Returns
    -------
    topology : Topology
        The cluster-level topology

    Notes
    -----
     * Each router must have a cache deployed
     * All sources and receiver must have one single attachment point with a
       cache
     * Each node must be labelled with cluster
    """
    cluster_map = nx.get_node_attributes(topology, 'cluster')
    if len(cluster_map) < topology.number_of_nodes():
        raise ValueError('There are nodes not labelled with cluster information')
    if nx.number_connected_components(topology) > 1:
        raise ValueError('There is more than one connected component')
    cluster_topology = fnss.Topology()
    cluster_set = set(cluster_map.values())
    if len(cluster_set) == 1:
        # There is only one huge cluster
        cluster_topology.add_node(cluster_set.pop())
        return cluster_topology
    for u, v in topology.edges():
        cluster_u = cluster_map[u]
        cluster_v = cluster_map[v]
        if cluster_u != cluster_v:
            cluster_topology.add_edge(cluster_u, cluster_v)
    return cluster_topology


def deploy_clusters(topology, clusters, assign_src_rcv=True):
    """Annotate topology with cluster informations

    This function checks that all ICR candidate nodes are assigned exactly
    to one cluster.

    If assign_src_rcv is True, then it also labels source and receiver nodes
    to the closest cluster.

    This function assumes that:
     * each node of the topology is either an icr_candidate, a source or a receiver
     * each source and receiver must have degree equal to 1

    Parameters
    ----------
    topology : Topology
        The topology onto which deploy clusters
    clusters : list of sets
        Router-cluster assignment. Each element of a list is a set of node
        identifiers. Nodes in the same set belong to the same cluster.
        The length of the list therefore corresponds to the number of clusters.
    assign_src_rcv : bool, optional
        If *True*, the function labels source and receiver nodes with the
        cluster label of the router they are attached to.
    """
    clustered_nodes = set()
    n_clustered_nodes = 0
    for c in clusters:
        clustered_nodes = clustered_nodes.union(c)
        n_clustered_nodes += len(c)
    if n_clustered_nodes != len(clustered_nodes):
        raise ValueError('At least one node is listed in more than one cluster')
    if clustered_nodes != topology.graph['icr_candidates']:
        raise ValueError('Set of nodes in the cluster do not match ICR candidates')
    topology.graph['clusters'] = clusters
    for i in range(len(clusters)):
        for v in clusters[i]:
            topology.node[v]['cluster'] = i
    if not assign_src_rcv:
        return
    src_rcv = topology.sources().union(topology.receivers())
    deg = nx.degree(topology)
    if any(deg[v] > 1 for v in src_rcv):
        raise ValueError("There are at least one source or receiver with degree >= 1")
    for v in src_rcv:
        next_node = list(topology.adj[v].keys())[0]
        topology.node[v]['cluster'] = topology.node[next_node]['cluster']


def compute_clusters(topology, k, distance='delay', nbunch=None, n_iter=10):
    """Cluster nodes of a topologies as to minimize the intra-cluster latency.

    This function assumes that every link is labelled with latencies and
    performs clustering using the k-medoids method with the PAM algorithm.

    Parameters
    ----------
    topology : Topology
        The topology
    k : int
        The number of clusters
    distance : str, optional
        The link metric used to represent distance between nodes.
        If None, hop count is used instead
    n_iter : int, optional
        The number of iterations

    Return
    ------
    clusters: list of sets
        List of clusters (each cluster being a set of nodes)
    """
    topology = topology.to_undirected()
    if nx.number_connected_components(topology) > 1:
        raise ValueError('The topology has more than one connected component')
    if nbunch is not None:
        topology = topology.subgraph(nbunch)
    topology = nx.convert_node_labels_to_integers(topology, label_attribute='label')

    if distance is not None:
        for u, v in topology.edges():
            if distance not in topology.adj[u][v]:
                raise ValueError('Edge (%s, %s) does not have a %s attribute'
                                 % (str(topology.node[u]['label']),
                                    str(topology.node[v]['label']),
                                    distance))

    n = topology.number_of_nodes()
    path = dict(nx.all_pairs_shortest_path(topology))
    distances = np.zeros((n, n))

    for u in path:
        for v in path[u]:
            # Note: need to do something about weights and asymmetric paths!
            if u == v or distances[u][v] != 0:
                continue
            # Extract all edges of a path
            edges = path_links(path[u][v])
            if distance is not None:
                distances[u][v] = distances[v][u] = sum(topology.adj[u][v][distance]
                                                        for u, v in edges)
            else:
                distances[u][v] = distances[v][u] = len(edges)
    clusters = [set() for _ in range(k)]
    medoid_assignment = pam(distances, k=k, n_iter=n_iter)[0]
    if any(medoid_assignment >= n):
        raise ValueError('Something is wrong with k-medoids algorithm. '
                         'I got an assignment to a medoid that does not exist')
    medoids = list(set(medoid_assignment))
    medoid_cluster_map = {medoids[i]: i for i in range(len(medoids))}
    # Concert assignments from medoid ID to cluster ID
    for v in range(n):
        clusters[medoid_cluster_map[medoid_assignment[v]]].add(topology.node[v]['label'])
    return clusters


def compute_p_median(distances, p, n_iter=20):
    """Compute p-median solution using the Adjusted Vertex Substitution (AVS)
    algorithm.

    Parameters
    ----------
    distances : dict of dicts
        Distance between nodes
    p : int
        Number of facilities

    Return
    ------
    allocation : dict
        Dict mapping each node to the allocated facility
    facilities : set
        Set of the p facilities identified
    """
    if p > len(distances):
        raise ValueError("p value is greater than the number of points")
    distances_matrix = np.zeros((len(distances), len(distances)))
    nodes = list(sorted(distances.keys()))
    nodes_map = dict(list(enumerate(nodes)))
    for i, v in enumerate(nodes):
        for j, u in enumerate(nodes):
            distances_matrix[i][j] = distances[u][v]
    mappings, medians, cost = pam(distances_matrix, p, n_iter=n_iter)
    facilities = set(nodes_map[v] for v in medians)
    allocation = {}
    for i, j in enumerate(mappings):
        allocation[nodes_map[i]] = nodes_map[j]
    return allocation, facilities, cost
