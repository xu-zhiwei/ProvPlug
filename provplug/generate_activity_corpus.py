from activity_corpus_generation import *
from parser import build_undirected_graph
import random


def generate_activity_corpus(
    start_node,
    edges,
    graph,
    component_sizes,
    neighbor_count,
    max_sequence_length,
    random_prop,
):
    # Perform a depth-first walk
    walk_sequence = depth_first_walker(
        start_node,
        max_sequence_length,
        graph,
        component_sizes,
        neighbor_count,
        random_prop,
    )

    # Construct neighborhood graph
    context = neighborhood_graph_construction(walk_sequence, edges)

    # Temporal sorting and natural language alignment
    natural_language_text = temporal_sorter(context)

    return natural_language_text


if __name__ == "__main__":
    # Example hyperparameters
    random_seed = 42

    max_sequence_length = 10
    random_prop = 0.2
    process_count = 32

    input_jsonl_path = "xxx.jsonl"

    # Set the random seed for reproducibility
    set_random_seed(random_seed)

    # Read edges and build the graph
    edges = read_edges(input_jsonl_path)
    graph = build_undirected_graph(edges)

    # Prepare for depth-first walks
    component_sizes = compute_connected_components(graph)
    neighbor_count = {node: len(neighbors) for node, neighbors in graph.items()}
    start_node = random.choice(list(graph.keys()))

    # Generate activity corpus
    natural_language_text = generate_activity_corpus(
        start_node,
        edges,
        graph,
        component_sizes,
        neighbor_count,
        max_sequence_length,
        random_prop,
    )

    print("Activity Corpus:")
    print(natural_language_text)
