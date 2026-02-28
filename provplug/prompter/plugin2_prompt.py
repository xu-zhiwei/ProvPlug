def get_plugin2_prompt():
    prompt = """Based on the analysis, please assign scores to each of the three dimensions. The scores assigned must be discriminatively distributed within the range of 0 to 5. The output must be a json format: {"temporal_score": %.2f, "contextual_score": %.2f, "propagational_score": %.2f}."""
    return prompt
