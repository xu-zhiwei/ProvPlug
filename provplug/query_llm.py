from prompter import *
import requests
import json


def _plugin1_prompting(natural_language_text):
    """Plugin1 prompting"""
    provenance_semantic_prompt = get_provenance_semantic_prompt()
    plugin1_prompt = get_plugin1_prompt()
    query = f"{provenance_semantic_prompt}\n{plugin1_prompt}\n{natural_language_text}"
    return query


def _plugin2_prompting(natural_language_text):
    """Plugin2 prompting"""
    provenance_semantic_prompt = get_provenance_semantic_prompt()
    plugin2_prompt = get_plugin2_prompt()
    query = f"{provenance_semantic_prompt}\n{plugin2_prompt}\n{natural_language_text}"
    return query


def _query_llm(query):
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": query}],
        "max_tokens": MAX_TOKENS,
        "temperature": TEMPERATURE,
        "top_p": TOP_P,
        "top_k": 20,
    }
    headers = {
        "Authorization": "Bearer YOUR_API_KEY"  # Do not need to change for local vLLM
    }
    try:
        r = requests.post(
            f"{API_URL}/chat/completions", json=payload, headers=headers, timeout=600
        )
        if r.status_code != 200:
            raise RuntimeError(f"HTTP {r.status_code}: {r.text[:300]}")
        data = r.json()
        if "choices" not in data:
            raise KeyError(f"Response missing 'choices': {json.dumps(data)[:300]}")
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"[API call failed] {e}"


def query_llm_using_plugin(natural_language_text, plugin_name="Plugin1"):
    if plugin_name == "Plugin1":
        query = _plugin1_prompting(natural_language_text)
    else:
        query = _plugin2_prompting(natural_language_text)
    response = _query_llm(query)
    return response


if __name__ == "__main__":
    # Example input activity corpus
    input_activity_corpus = "REPLACE_WITH_ACTIVITY_CORPUS"

    # Example vLLM API parameters
    API_URL = "http://192.168.2.6:8000/v1"
    MODEL = "Qwen/Qwen3-30B-A3B-Instruct-2507"
    MAX_TOKENS = 32768
    TEMPERATURE = 0.8
    TOP_P = 0.95

    # Example usage with Plugin1 and Plugin2
    query_llm_using_plugin(input_activity_corpus, "Plugin1")
    query_llm_using_plugin(input_activity_corpus, "Plugin2")
