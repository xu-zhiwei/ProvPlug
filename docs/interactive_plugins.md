# Documentation for Interactive Plugins in ProvPlug

## Plugin1

To interactively use Plugin1, follow these steps:

1. Extract start nodes from a batch of graph data.
2. Perform multi-round workflows involving walks and LLM analysis. Please refer to `src/interactive_plugin1.py` for implementation details. Replace start nodes with your extracted nodes.
3. Extract adding edges from the batch of graph data.
4. Add those edges to the batch of graph data.

## Plugin2

To interactively use Plugin2, follow these steps:

1. Extract all nodes from a batch of substructures.
2. Randomly select a portion of nodes as start nodes based on the substructures.
3. Perform multi-round workflows involving walks and LLM analysis. Please refer to `src/interactive_plugin2.py` for implementation details. Replace start nodes with your selected nodes.
4. Compute normalized training guidance scores based on the LLM analysis of discovered walks. The scores will be in the range of [0.5, 1.5], where lower original scores correspond to higher normalized scores.
5. Return the normalized scores for backward propagation.