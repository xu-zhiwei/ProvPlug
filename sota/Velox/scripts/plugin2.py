#!/usr/bin/env python3
"""
Parse result files of LLM's responses. Calculate weighted average scores for each edge type, and scale them to the 0.5-1.5 range.

The main steps are:
1. Iterate through LLM result files
2. Extract the occurrence count and average of three scores for each edge type (EVENT_TYPE)
3. Compute weighted average across different files based on occurrence counts
4. Scale to 0.5-1.5 range using formula: 0.5 + (max - value) / (max - min)
5. Filter to only 10 standard edge types and output weight array in the order of rel2id_darpa_tc (this is for compatibility with the velox's edge type)
"""

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, Tuple

# Standard edge type order (according to rel2id_darpa_tc of velox codebase)
STANDARD_EDGE_TYPES = [
    "EVENT_CONNECT",    # 1
    "EVENT_EXECUTE",    # 2
    "EVENT_OPEN",       # 3
    "EVENT_READ",       # 4
    "EVENT_RECVFROM",   # 5
    "EVENT_RECVMSG",    # 6
    "EVENT_SENDMSG",    # 7
    "EVENT_SENDTO",     # 8
    "EVENT_WRITE",      # 9
    "EVENT_CLONE",      # 10
]


def extract_json_from_text(text: str) -> dict:
    """Extract JSON object from text"""
    # First try to find JSON in code blocks (```json ... ```)
    code_block_match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
    if code_block_match:
        try:
            return json.loads(code_block_match.group(1))
        except json.JSONDecodeError:
            pass
    
    # Find JSON object (may span multiple lines)
    json_match = re.search(r'\{[^{}]*"temporal_score"[^{}]*\}', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
    
    # Try to find all possible JSON blocks
    json_pattern = r'\{[^{}]*\}'
    matches = re.findall(json_pattern, text, re.DOTALL)
    for match in matches:
        try:
            data = json.loads(match)
            if "temporal_score" in data or "contextual_score" in data or "propagational_score" in data:
                return data
        except json.JSONDecodeError:
            continue
    
    return {}


def parse_result_file(file_path: Path) -> Tuple[Dict[str, int], float]:
    """
    Parse a single result file
    
    Returns:
        (event_type_counts, average_score): 
        - event_type_counts: Dictionary mapping edge type -> occurrence count
        - average_score: Average of three scores
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract JSON scores
    json_data = extract_json_from_text(content)
    
    if not json_data:
        print(f"  Warning: Could not parse scores from {file_path.name}")
        return {}, 0.0
    
    # Get three scores (note: field name may be propagational_score or propagation_score)
    temporal_score = json_data.get("temporal_score", 0.0)
    contextual_score = json_data.get("contextual_score", 0.0)
    propagational_score = json_data.get("propagational_score")
    
    # Calculate average score
    average_score = (temporal_score + contextual_score + propagational_score) / 3.0
    
    # Extract event types (edge types)
    # Find all lines in format: subject,EVENT_TYPE,object
    event_type_pattern = r',([A-Z_]+),'
    event_types = re.findall(event_type_pattern, content)
    
    # Count occurrences of each edge type
    event_type_counts: Dict[str, int] = defaultdict(int)
    for event_type in event_types:
        if event_type.startswith("EVENT_"):
            event_type_counts[event_type] += 1
    
    return dict(event_type_counts), average_score


def process_dataset(dataset_dir: Path) -> Dict[str, Dict]:
    """
    Process all result files in a single dataset directory
    
    Returns:
        Dictionary with edge type as key, value contains:
        - count: Total occurrence count
        - weighted_avg_score: Weighted average score
        - scaled_score: Scaled score (calculated later)
    """
    print(f"\nProcessing dataset: {dataset_dir.name}")
    
    # Statistics for each edge type
    # event_type_stats[event_type] = {
    #     "total_weighted_score": sum(avg_score * count for each file),
    #     "total_weight": sum(count for each file)
    # }
    event_type_stats: Dict[str, Dict[str, float]] = defaultdict(lambda: {
        "total_weighted_score": 0.0,
        "total_weight": 0.0
    })
    
    # Get all result files
    result_files = sorted(dataset_dir.glob("*.txt"))
    print(f"  Found {len(result_files)} result files")
    
    processed_files = 0
    for result_file in result_files:
        try:
            event_type_counts, avg_score = parse_result_file(result_file)
            
            if not event_type_counts:
                continue
            
            # Update statistics (weighted average)
            for event_type, count in event_type_counts.items():
                event_type_stats[event_type]["total_weighted_score"] += avg_score * count
                event_type_stats[event_type]["total_weight"] += count
            
            processed_files += 1
        except Exception as e:
            print(f"  Error processing {result_file.name}: {e}")
            continue
    
    print(f"  Successfully processed {processed_files} files")
    
    # Calculate weighted average score
    result = {}
    for event_type, stats in event_type_stats.items():
        if stats["total_weight"] > 0:
            weighted_avg_score = stats["total_weighted_score"] / stats["total_weight"]
            result[event_type] = {
                "count": int(stats["total_weight"]),
                "weighted_avg_score": weighted_avg_score
            }
    
    return result


def scale_scores(event_type_scores: Dict[str, Dict]) -> Dict[str, Dict]:
    """
    Scale scores to 0.5-1.5 range using formula: 0.5 + (max - value) / (max - min)
    
    Note: This formula maps higher scores to lower values (because of max - value)
    If max is the highest score, then the highest score will be mapped to 0.5, and the lowest score will be mapped to 1.5
    
    Only process edge types with actual data (count > 0)
    """
    if not event_type_scores:
        return {}
    
    # Extract all weighted average scores (only consider edge types with data)
    scores = [
        stats["weighted_avg_score"] 
        for stats in event_type_scores.values() 
        if stats.get("count", 0) > 0
    ]
    
    if not scores:
        # If no valid scores, set default values
        for event_type in event_type_scores:
            event_type_scores[event_type]["scaled_score"] = 1.0
        return event_type_scores
    
    min_score = min(scores)
    max_score = max(scores)
    
    # If all scores are the same, avoid division by zero
    if max_score == min_score:
        print(f"  Warning: All scores are the same ({min_score}), setting scaled_score to 1.0")
        for event_type in event_type_scores:
            if event_type_scores[event_type].get("count", 0) > 0:
                event_type_scores[event_type]["scaled_score"] = 1.0
            else:
                event_type_scores[event_type]["scaled_score"] = 1.0
        return event_type_scores
    
    # Apply scaling formula: 0.5 + (max - value) / (max - min)
    # This maps max_score to 0.5, min_score to 1.5
    for event_type, stats in event_type_scores.items():
        if stats.get("count", 0) > 0:
            value = stats["weighted_avg_score"]
            scaled_score = 0.5 + (max_score - value) / (max_score - min_score)
            stats["scaled_score"] = scaled_score
        else:
            # For edge types without data, use default value 1.0
            stats["scaled_score"] = 1.0
    
    return event_type_scores


def filter_to_standard(event_type_stats: Dict[str, Dict]) -> Dict[str, Dict]:
    """
    Keep only the standard 10 edge types. Edge types not in the list will be discarded.
    Missing edge types will be filled in with default values: count=0, weighted_avg_score=0.0, scaled_score=1.0
    """
    filtered = {}
    for edge_type in STANDARD_EDGE_TYPES:
        if edge_type in event_type_stats:
            filtered[edge_type] = event_type_stats[edge_type]
        else:
            filtered[edge_type] = {
                "count": 0,
                "weighted_avg_score": 0.0,
                "scaled_score": 1.0,
            }
    return filtered


def main():
    """Main function"""
    # Results directory
    results_dir = "/path/to/your/results"
    
    if not results_dir.exists():
        print(f"Error: Results directory does not exist: {results_dir}")
        return
    
    print(f"Results directory: {results_dir}")
    
    # Process each dataset (filter first, then scale, ensuring min/max based on 10 standard types)
    filtered_results = {}
    weight_arrays = {}
    
    for dataset_dir in sorted(results_dir.iterdir()):
        if not dataset_dir.is_dir():
            continue
        
        dataset_name = dataset_dir.name
        
        # Process this dataset to get statistics for all edge types
        dataset_results = process_dataset(dataset_dir)
        
        if not dataset_results:
            continue
        
        # Keep only the standard 10 edge types, then scale
        filtered_stats = filter_to_standard(dataset_results)
        filtered_stats = scale_scores(filtered_stats)
        
        # Generate weight array in standard order
        weight_array = [filtered_stats[et]["scaled_score"] for et in STANDARD_EDGE_TYPES]
        
        filtered_results[dataset_name] = filtered_stats
        weight_arrays[dataset_name] = weight_array
    
    # Print results
    print("\n" + "=" * 80)
    print("Results Summary (Standard Edge Types Only)")
    print("=" * 80)
    
    for dataset_name, event_type_stats in sorted(filtered_results.items()):
        print(f"\nDataset: {dataset_name}")
        print("-" * 80)
        print(f"{'Edge Type':<30} {'Occurrences':<12} {'Weighted Avg Score':<18} {'Scaled Score':<15}")
        print("-" * 80)
        
        # Output in standard order
        for edge_type in STANDARD_EDGE_TYPES:
            stats = event_type_stats[edge_type]
            print(
                f"{edge_type:<30} "
                f"{stats['count']:<12} "
                f"{stats['weighted_avg_score']:<18.4f} "
                f"{stats['scaled_score']:<15.4f}"
            )
        
        # Print weight array
        print(f"\nWeight Array: {weight_arrays[dataset_name]}")
    
    # Save results to JSON file
    output_file = results_dir.parent / "edge_weights.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(filtered_results, f, indent=2, ensure_ascii=False)
    
    # Save weight arrays to JSON file
    weights_array_file = results_dir.parent / "edge_weights_array.json"
    with open(weights_array_file, 'w', encoding='utf-8') as f:
        json.dump(weight_arrays, f, indent=2, ensure_ascii=False)
    
    print(f"\nResults saved to: {output_file}")
    print(f"Weight arrays saved to: {weights_array_file}")
    
    # Generate summary statistics
    print("\n" + "=" * 80)
    print("Cross-Dataset Summary (Edge Type Statistics Across All Datasets)")
    print("=" * 80)
    
    # Merge edge types from all datasets (standard edge types only)
    global_event_stats: Dict[str, Dict] = {}
    
    for dataset_name, event_type_stats in filtered_results.items():
        for event_type in STANDARD_EDGE_TYPES:
            if event_type not in event_type_stats:
                continue
            
            stats = event_type_stats[event_type]
            if event_type not in global_event_stats:
                global_event_stats[event_type] = {
                    "total_count": 0,
                    "total_weighted_score": 0.0,
                    "datasets": set()
                }
            
            global_event_stats[event_type]["total_count"] += stats["count"]
            global_event_stats[event_type]["total_weighted_score"] += (
                stats["weighted_avg_score"] * stats["count"]
            )
            global_event_stats[event_type]["datasets"].add(dataset_name)
    
    # Calculate global weighted average (standard edge types only)
    global_results: Dict[str, Dict] = {}
    for event_type in STANDARD_EDGE_TYPES:
        if event_type in global_event_stats:
            stats = global_event_stats[event_type]
            if stats["total_count"] > 0:
                global_weighted_avg = stats["total_weighted_score"] / stats["total_count"]
                global_results[event_type] = {
                    "count": stats["total_count"],
                    "weighted_avg_score": global_weighted_avg,
                    "datasets": sorted(list(stats["datasets"]))
                }
            else:
                global_results[event_type] = {
                    "count": 0,
                    "weighted_avg_score": 0.0,
                    "datasets": []
                }
        else:
            global_results[event_type] = {
                "count": 0,
                "weighted_avg_score": 0.0,
                "datasets": []
            }
    
    # Scale global scores
    global_results = scale_scores(global_results)
    
    # Generate global weight array
    global_weight_array = [global_results[et]["scaled_score"] for et in STANDARD_EDGE_TYPES]
    
    print(f"\n{'Edge Type':<30} {'Total Occurrences':<15} {'Weighted Avg Score':<18} {'Scaled Score':<15} {'Num Datasets':<10}")
    print("-" * 100)
    
    # Output in standard order
    for event_type in STANDARD_EDGE_TYPES:
        stats = global_results[event_type]
        print(
            f"{event_type:<30} "
            f"{stats['count']:<15} "
            f"{stats['weighted_avg_score']:<18.4f} "
            f"{stats['scaled_score']:<15.4f} "
            f"{len(stats['datasets']):<10}"
        )
    
    print(f"\nGlobal Weight Array: {global_weight_array}")
    
    # Save global results
    global_output_file = results_dir.parent / "edge_weights_global.json"
    with open(global_output_file, 'w', encoding='utf-8') as f:
        json.dump(global_results, f, indent=2, ensure_ascii=False)
    
    # Save global weight array
    global_array_file = results_dir.parent / "edge_weights_global_array.json"
    with open(global_array_file, 'w', encoding='utf-8') as f:
        json.dump({"weights": global_weight_array}, f, indent=2, ensure_ascii=False)
    
    print(f"\nGlobal results saved to: {global_output_file}")
    print(f"Global weight array saved to: {global_array_file}")


if __name__ == "__main__":
    main()