import json
from collections import deque
import random


def set_random_seed(seed=42):
    """Set the random seed for reproducibility."""
    random.seed(seed)


def read_edges(filename):
    """Parse edges from the unified JSONL file."""
    edges = []
    with open(filename, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                edges.append(
                    {
                        "line": line_num,  # choronlogical line number sorted by timestamp
                        "subject": data["subject"],
                        "event": data["event"],
                        "object": data["object"],
                    }
                )
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Line {line_num}: skipped ({e.__class__.__name__})")
    return edges


def read_nodes(filename):
    """Read nodes from a text file."""
    nodes = []
    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            node = line.strip()
            if node:
                nodes.append(node)
    return nodes


def compute_connected_components(graph):
    """Compute connected components in the graph."""
    visited = set()
    component_sizes = {}
    components = []

    for node in graph:
        if node not in visited:
            queue = deque([node])
            visited.add(node)
            component = [node]

            while queue:
                current = queue.popleft()
                for neighbor in graph[current]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        component.append(neighbor)
                        queue.append(neighbor)

            component_size = len(component)
            components.append((component, component_size))

            for n in component:
                component_sizes[n] = component_size

    print(f"Found {len(components)} connected components")
    return component_sizes
