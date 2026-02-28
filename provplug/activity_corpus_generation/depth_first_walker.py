import random


def depth_first_walker(
    start_node, max_length, graph, component_sizes, neighbor_count, random_prop
):
    """Depth-first walker with prioritized neighbor selection.
    
    Args:
        start_node: Starting node for the walk
        max_length: Maximum walk length
        graph: Adjacency list representation of the graph
        component_sizes: Size of connected component for each node
        neighbor_count: Degree count for each node
        random_prop: Probability threshold for random vs priority-based selection
    """
    # Handle isolated nodes
    if start_node not in graph:
        return [start_node]

    # Limit walk length to component size to avoid invalid traversals
    component_size = component_sizes.get(start_node, 1)
    actual_max_length = min(max_length, component_size)
    if actual_max_length == 1:
        return [start_node]

    walk_sequence = [start_node]
    visited = set(walk_sequence)
    current_node = start_node
    walk_len = 1

    while walk_len < actual_max_length:
        neighbors = graph[current_node]
        next_node = None

        # Priority-based selection: prefer neighbors that form triangles with parent node
        if walk_len >= 2 and random.random() >= random_prop:
            parent_node = walk_sequence[-2]
            top_priority = None
            top_candidates = []

            # Iterate through neighbors and calculate multi-level priorities
            for neighbor in neighbors:
                # Priority Level 1: Distance to parent (prefer triangles and 2-hops)
                if neighbor == parent_node:
                    dist_priority = 0
                elif parent_node in graph[neighbor]:
                    dist_priority = 1
                else:
                    dist_priority = 2

                # Priority Level 2: Unvisited neighbor ratio (prefer nodes with more exploration potential)
                neighbor_degree = neighbor_count.get(neighbor, 1)
                max_degree = max(neighbor_degree, 1)
                unvisited_neighbor_num = sum(
                    1 for n in graph[neighbor] if n not in visited
                )
                neighbor_unvisited_ratio = unvisited_neighbor_num / max_degree

                # Priority Level 3: Node degree (prefer high-degree hubs)
                degree_priority = neighbor_count.get(neighbor, 0)

                # Tuple comparison: (dist, unvisited_ratio, degree) in descending order
                current_priority = (
                    dist_priority,
                    neighbor_unvisited_ratio,
                    degree_priority,
                )

                # Track candidates with highest priority (efficient single-pass selection)
                if top_priority is None:
                    top_priority = current_priority
                    top_candidates = [neighbor]
                else:
                    if current_priority > top_priority:
                        top_priority = current_priority
                        top_candidates = [neighbor]
                    elif current_priority == top_priority:
                        top_candidates.append(neighbor)

            # Randomly select from top-priority candidates
            if top_candidates:
                next_node = random.choice(top_candidates)
            else:
                next_node = random.choice(list(neighbors))
        # Random selection: low random probability
        else:
            next_node = random.choice(list(neighbors))

        walk_sequence.append(next_node)
        visited.add(next_node)
        current_node = next_node
        walk_len += 1

    return walk_sequence
