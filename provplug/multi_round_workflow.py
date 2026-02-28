from .generate_activity_corpus import generate_activity_corpus
from .query_llm import query_llm_using_plugin
from activity_corpus_generation import *
from multiprocessing import Pool
from tqdm import tqdm


def workflow(args):
    (
        start_node,
        edges,
        graph,
        component_sizes,
        neighbor_count,
        max_sequence_length,
        random_prop,
        plugin_name,
    ) = args

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

    # Interact with LLM
    response = query_llm_using_plugin(natural_language_text, plugin_name)

    return natural_language_text, response


def multi_round_workflow(
    start_nodes,
    edges,
    graph,
    component_sizes,
    neighbor_count,
    max_sequence_length,
    random_prop,
    process_count,
    plugin_name,
):
    # Multiprocessing workflow execution with a large mount of start nodes
    task_args = []
    for start_node in start_nodes:
        task_args = (
            start_node,
            edges,
            graph,
            component_sizes,
            neighbor_count,
            max_sequence_length,
            random_prop,
            plugin_name,
        )
        task_args.append(task_args)

    with Pool(processes=process_count) as pool:
        results = list(
            tqdm(
                pool.map(workflow, task_args),
                total=len(task_args),
                desc="Multiprocessing Workflow",
            )
        )
        natural_language_texts, responses = zip(*results)

    return natural_language_texts, responses
