from .multi_round_workflow import multi_round_workflow
from activity_corpus_generation import *
from parser import build_undirected_graph
import random
import re
import json


def _extract_json_objects(content):
    """
    Extract JSON objects from the file content
    """
    # Find the JSON part (usually after the blank line)
    lines = content.split("\n")
    json_start = -1

    for i, line in enumerate(lines):
        if line.strip() == "":
            json_start = i + 1
            break

    if json_start == -1:
        return []

    json_content = "\n".join(lines[json_start:])

    # Use regular expressions to match JSON arrays
    json_match = re.search(r"\[.*\]", json_content, re.DOTALL)
    if not json_match:
        return []

    try:
        json_str = json_match.group(0)
        # Clean up comments and trailing commas in the JSON string
        json_str = re.sub(r"//.*", "", json_str)  # Remove single-line comments
        json_str = re.sub(r",\s*}", "}", json_str)  # Fix trailing commas (object level)
        json_str = re.sub(r",\s*]", "]", json_str)  # Fix trailing commas (array level)

        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        return []


def extract_adding_edges(query_results, confidence_threshold=0):
    adding_edges = set()
    for result in query_results:
        json_object = _extract_json_objects(result)
        for edge in json_object:
            if edge['confidence_level'] < confidence_threshold:
                continue
            adding_edges.add((edge['entity1'], edge['entity2']))
    return adding_edges


def main():
    # Example hyperparameters
    random_seed = 42

    max_sequence_length = 10
    random_prop = 0.2
    process_count = 32

    plugin_name = "Plugin1"

    input_jsonl_path = "xxx.jsonl"
    input_start_nodes = None
    num_prop = 0.001

    # Set the random seed for reproducibility
    set_random_seed(random_seed)

    # Read edges and build the graph
    edges = read_edges(input_jsonl_path)
    graph = build_undirected_graph(edges)

    # Prepare for depth-first walks
    component_sizes = compute_connected_components(graph)
    neighbor_count = {node: len(neighbors) for node, neighbors in graph.items()}
    all_nodes = list(graph.keys())

    if input_start_nodes is not None:
        start_nodes = read_nodes(input_start_nodes)
    else:
        start_nodes = random.choices(all_nodes, k=int(len(all_nodes) * num_prop))

    _, responses = multi_round_workflow(
        start_nodes,
        edges,
        graph,
        component_sizes,
        neighbor_count,
        max_sequence_length,
        random_prop,
        process_count,
        plugin_name,
    )
    
    adding_edges = extract_adding_edges(responses, confidence_threshold=0)

    return adding_edges

if __name__ == "__main__":
    main()
