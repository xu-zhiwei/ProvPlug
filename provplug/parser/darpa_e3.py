import re
import os
import json
from typing import Optional, Dict, List, Tuple


UUID_PATTERN = re.compile(r'uuid\":\"(.*?)\"')
TYPE_PATTERN = re.compile(r'type\":\"(.*?)\"')
SRC_PATTERN = re.compile(r'subject\":{\"com.bbn.tc.schema.avro.cdm18.UUID\":\"(.*?)\"}')
DST1_PATTERN = re.compile(r'predicateObject\":{\"com.bbn.tc.schema.avro.cdm18.UUID\":\"(.*?)\"}')
DST2_PATTERN = re.compile(r'predicateObject2\":{\"com.bbn.tc.schema.avro.cdm18.UUID\":\"(.*?)\"}')
TIMESTAMP_PATTERN = re.compile(r'timestampNanos\":(.*?),')

EVENT_TYPE = 'com.bbn.tc.schema.avro.cdm18.Event'
HOST_TYPE = 'com.bbn.tc.schema.avro.cdm18.Host'
TIME_MARKER_TYPE = 'com.bbn.tc.schema.avro.cdm18.TimeMarker'
START_MARKER_TYPE = 'com.bbn.tc.schema.avro.cdm18.StartMarker'
UNIT_DEPENDENCY_TYPE = 'com.bbn.tc.schema.avro.cdm18.UnitDependency'
END_MARKER_TYPE = 'com.bbn.tc.schema.avro.cdm18.EndMarker'
MEMORY_OBJECT_TYPE = 'com.bbn.tc.schema.avro.cdm18.MemoryObject'
NETFLOW_OBJECT_TYPE = 'com.bbn.tc.schema.avro.cdm18.NetFlowObject'
UNNAMED_PIPE_OBJECT_TYPE = 'com.bbn.tc.schema.avro.cdm18.UnnamedPipeObject'

REPORT_INTERVAL = 1000000

def extract_uuid(line: str) -> Optional[str]:
    matches = UUID_PATTERN.findall(line)
    return matches[0] if matches else None


def extract_subject_type(line: str) -> Optional[str]:
    matches = TYPE_PATTERN.findall(line)
    return matches[0] if matches else None

def extract_edge_info(line: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[str]]:
    edge_type = extract_subject_type(line)
    if not edge_type:
        return None, None, None, None, None

    timestamp_matches = TIMESTAMP_PATTERN.findall(line)
    if not timestamp_matches:
        return None, None, None, None, None
    timestamp = timestamp_matches[0]

    src_matches = SRC_PATTERN.findall(line)
    if not src_matches:
        return None, None, None, None, None
    src_id = src_matches[0]

    def extract_dest_id(pattern) -> Optional[str]:
        matches = pattern.findall(line)
        return matches[0] if matches and matches[0] != 'null' else None

    dst_id1 = extract_dest_id(DST1_PATTERN)
    dst_id2 = extract_dest_id(DST2_PATTERN)

    return src_id, edge_type, timestamp, dst_id1, dst_id2


SKIP_TYPES = [EVENT_TYPE, HOST_TYPE, TIME_MARKER_TYPE, START_MARKER_TYPE,
              UNIT_DEPENDENCY_TYPE, END_MARKER_TYPE]

SPECIAL_OBJECTS = {
    MEMORY_OBJECT_TYPE: 'MemoryObject',
    NETFLOW_OBJECT_TYPE: 'NetFlowObject',
    UNNAMED_PIPE_OBJECT_TYPE: 'UnnamedPipeObject'
}

def _should_skip_line(line: str) -> bool:
    """Check if line should be skipped during processing"""
    return any(skip_type in line for skip_type in SKIP_TYPES)

def _extract_special_object_type(line: str) -> Optional[str]:
    """Extract special object type if present"""
    for object_type, type_name in SPECIAL_OBJECTS.items():
        if object_type in line:
            return type_name
    return None

def process_data(file_path: str, id_nodetype_map: Dict[str, str]) -> Dict[str, str]:
    """Parse node data from CDM18 records and build ID to node type mapping"""
    for file_index in range(100):
        current_path = file_path if file_index == 0 else f"{file_path}.{file_index}"

        if not os.path.exists(current_path):
            break

        with open(current_path, 'r') as f:
            line_count = 0
            for line in f:
                line_count += 1
                if line_count % REPORT_INTERVAL == 0:
                    print(f"Processed {line_count} lines")

                if _should_skip_line(line):
                    continue

                node_id = extract_uuid(line)
                if not node_id:
                    continue

                node_type = extract_subject_type(line)

                if not node_type:
                    special_type = _extract_special_object_type(line)
                    if special_type:
                        id_nodetype_map[node_id] = special_type
                else:
                    id_nodetype_map[node_id] = node_type

    return id_nodetype_map

# Extract and sort edges from event records by timestamp
def _add_edge(edges: List[Dict], src_id: str, edge_type: str,
              dest_id: Optional[str], timestamp: str, id_nodetype_map: Dict) -> None:
    if dest_id and dest_id in id_nodetype_map:
        edges.append({
            "subject": src_id,
            "event": edge_type,
            "object": dest_id,
            "timestamp": int(timestamp)
        })

def process_edges(file_path: str, id_nodetype_map: Dict[str, str]) -> None:
    edges: List[Dict] = []

    with open(file_path, 'r') as f:
        line_count = 0
        for line in f:
            line_count += 1
            if line_count % REPORT_INTERVAL == 0:
                print(f"Processed {line_count} lines")

            if EVENT_TYPE not in line:
                continue

            src_id, edge_type, timestamp, dst_id1, dst_id2 = extract_edge_info(line)

            if not src_id or src_id not in id_nodetype_map:
                continue

            _add_edge(edges, src_id, edge_type, dst_id1, timestamp, id_nodetype_map)
            _add_edge(edges, src_id, edge_type, dst_id2, timestamp, id_nodetype_map)

    edges.sort(key=lambda edge: edge["timestamp"])
    output_path = f"{file_path}.jsonl"
    written = set()
    with open(output_path, 'w') as output_file:
        for edge in edges:
            edge_key = (edge["subject"], edge["event"], edge["object"])
            if edge_key not in written:
                json_record = {
                    "subject": edge["subject"],
                    "event": edge["event"],
                    "object": edge["object"]
                }
                output_file.write(json.dumps(json_record) + '\n')
                written.add(edge_key)


def parse(data_files: List[str], edge_files: List[str]) -> None:
    node_type_map: Dict[str, str] = {}
    for data_file in data_files:
        process_data(data_file, node_type_map)
        print(f"Processed node data: {len(node_type_map)} nodes")

    for edge_file in edge_files:
        print(f"Processing edges from: {edge_file}")
        process_edges(edge_file, node_type_map)


if __name__ == "__main__":
    parse(
        data_files=['ta1-trace-e3-official-1.json'],
        edge_files=['ta1-trace-e3-official-1.json', 'ta1-trace-e3-official-1.json.4']
    )
