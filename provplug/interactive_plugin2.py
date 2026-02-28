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
    json_start = -1  # Locate where JSON data begins

    for i, line in enumerate(lines):
        if line.strip() == "":
            json_start = i + 1
            break

    if json_start == -1:
        return []

    json_content = "\n".join(lines[json_start:])

    # Use regular expressions to match JSON arrays
    json_match = re.search(r"\{.*\}", json_content, re.DOTALL)
    if not json_match:
        return []

    try:
        json_str = json_match.group(1) if len(json_match.groups()) > 0 else json_match.group(0)
        json_str = json_str.strip()

        # Parse JSON and extract three key scoring dimensions
        scores = json.loads(json_str)
        temporal = scores['temporal_score']
        contextual = scores['contextual_score']
        propagation = scores['propagational_score']
        # Compute average score across all three dimensions
        avg_score = (temporal + contextual + propagation) / 3.0
        
        return avg_score
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        return []
    

def _batch_normalization(scores):
    """
        Normalize scores to [0.5, 1.5] range using min-max scaling.
        Lower original scores correspond to higher normalized scores.
        Note that ProvPlug avoids changing loss functions, so it maps scores to [0.5, 1.5] instead of [0, 1].
    """
    if not scores:
        return []
    
    min_score = min(scores)
    max_score = max(scores)
    
    # Handle edge case where all scores are identical
    if min_score == max_score:
        return [0.5 for _ in scores]
    
    normalized_scores = [
        0.5 + (max_score - score) / (max_score - min_score) for score in scores
    ]
    
    return normalized_scores


def get_training_guidance_scores(substructures, natural_language_texts, query_results):
    """Calculate normalized training guidance scores for substructures based on LLM query results."""
    # Extract individual scores from LLM query results
    scores = []
    for result in query_results:
        score = _extract_json_objects(result)
        scores.append(score)
    
    # Aggregate scores for each substructure by counting node occurrences
    substructure_scores = [ ]
    for substructure in substructures:
        substructure_score = 0.
        for node in substructure:
            for natural_language_text, score in zip(natural_language_texts, scores):
                # Accumulate scores based on how frequently each node appears in NL text
                times = natural_language_text.count(node)
                substructure_score += times * score
        substructure_scores.append(substructure_score)
    
    normalized_scores = _batch_normalization(substructure_scores)

    return normalized_scores


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

    natural_language_texts, responses = multi_round_workflow(
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

    substructures = []  # REPLACE_WITH_SUBSTRUCTURES

    normalized_scores = get_training_guidance_scores(substructures, natural_language_texts, responses)

    return normalized_scores
    

if __name__ == "__main__":
    main()
