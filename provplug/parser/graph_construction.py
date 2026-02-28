from collections import defaultdict


def build_directed_graph(edges):
    """Build a directed graph from edges."""
    graph = defaultdict(set)
    for edge in edges:
        subject, obj = edge["subject"], edge["object"]
        graph[subject].add(obj)
    return graph


def build_undirected_graph(edges):
    """Build an undirected graph from edges."""
    graph = defaultdict(set)
    for edge in edges:
        subject, obj = edge["subject"], edge["object"]
        graph[subject].add(obj)
        graph[obj].add(subject)
    return graph
