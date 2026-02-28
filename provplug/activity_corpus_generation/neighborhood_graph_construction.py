def neighborhood_graph_construction(sequence, edges):
    """
    Filter edges from sequence nodes and sort by line number.
    This will construct a neighborhood graph for the given sequence of nodes,
    encompassing all edges related to those nodes.
    """
    nodes_in_sequence = set(sequence)
    relevant = [
        edge
        for edge in edges
        if edge["subject"] in nodes_in_sequence and edge["object"] in nodes_in_sequence
    ]
    return relevant
