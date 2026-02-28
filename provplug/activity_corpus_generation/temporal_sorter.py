def temporal_sorter(neighborhood_graph):
    """
    Sort the neighborhood graph.
    Align the events within the neighborhood graph with natural language sequences.
    """
    sorted = sorted(neighborhood_graph, key=lambda x: x["line"])
    natural_language_sentences = []
    for edge in sorted:
        subject = edge["subject"]
        event = edge["event"]
        object = edge["object"]
        sentence = f"{subject},{event},{object}."
        natural_language_sentences.append(sentence)
    natural_language_text = "\n".join(natural_language_sentences)
    return natural_language_text
