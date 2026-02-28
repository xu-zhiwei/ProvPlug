import time
import pandas as pd
import numpy as np
import os
import os.path as osp
import csv
import re
import json
import glob

def show(str):
	print (str + ' ' + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())))

def parse_llm_edges(edge_dir, id_nodetype_map, default_timestamp='0'):
	"""
	Parse LLM suggested edges from files in scripts/edge/{dataset}_train directory
	Supports trace, theia, cadets and other datasets
	
	:param edge_dir: Edge file directory path (e.g., scripts/edge/trace_train, scripts/edge/theia_train, scripts/edge/cadets_train)
	:param id_nodetype_map: Mapping from node ID to node type
	:param default_timestamp: Default timestamp (if not specified)
	:return: Edge list, each element is (srcId, srcType, dstId, dstType, edgeType, timestamp)
	"""
	llm_edges = []
	# Support new file naming format: {dataset}_train_result_*.txt
	edge_files = glob.glob(osp.join(edge_dir, '*_result_*.txt'))
	
	if not edge_files:
		show(f"Warning: No edge files found in {edge_dir}")
		return llm_edges
	
	show(f"Starting to parse LLM edge files, found {len(edge_files)} files")
	
	for edge_file in edge_files:
		try:
			with open(edge_file, 'r', encoding='utf-8') as f:
				content = f.read()
			
			# Find "--- 回答 ---" separator
			if '--- 回答 ---' not in content:
				continue
			
			# Extract JSON part
			# First find ```json code block
			json_start = content.find('```json')
			if json_start != -1:
				# Found code block start, find first [ or {
				json_start = content.find('[', json_start)
				if json_start == -1:
					json_start = content.find('{', content.find('```json'))
				json_end = content.find('```', json_start + 1)
				if json_end != -1:
					# Find last ] or } before code block end
					json_end = content.rfind(']', json_start, json_end)
					if json_end == -1:
						json_end = content.rfind('}', json_start, json_end)
					if json_end != -1:
						json_end += 1
			else:
				# No code block, directly find JSON start position
				json_start = content.find('[')
				if json_start == -1:
					json_start = content.find('{')
				
				if json_start != -1:
					# Find matching end position from start
					# Simple method: find last ] or } from back
					json_end = content.rfind(']')
					if json_end == -1 or json_end < json_start:
						json_end = content.rfind('}')
					if json_end != -1 and json_end >= json_start:
						json_end += 1
			
			if json_start == -1 or json_end == -1 or json_end <= json_start:
				continue
			
			json_str = content[json_start:json_end]
			
			# Parse JSON
			try:
				parsed_json = json.loads(json_str)
			except json.JSONDecodeError as e:
				show(f"Warning: Failed to parse JSON in {edge_file}: {e}")
				continue
			
			# Handle two formats:
			# 1. Direct array format: [{"subject": "...", "object": "...", "confidence level": ...}] or [{"entity1": "...", "entity2": "...", "confidence_level": ...}]
			# 2. Object format: {"causal_relations": [{"subject": "...", "object": "...", "confidence_level": ...}]} or {"causal_relations": [{"entity1": "...", "entity2": "...", "confidence_level": ...}]}
			edges_data = []
			if isinstance(parsed_json, list):
				# Direct array format
				edges_data = parsed_json
			elif isinstance(parsed_json, dict) and 'causal_relations' in parsed_json:
				# Object format, extract causal_relations field
				edges_data = parsed_json['causal_relations']
			
			# Process each edge
			for edge_data in edges_data:
				# Support multiple field name formats:
				# 1. 'subject' and 'object' (old format)
				# 2. 'entity1' and 'entity2' (new format)
				# 3. 'confidence level' and 'confidence_level'
				subject = edge_data.get('subject', edge_data.get('entity1', '')).strip()
				object_node = edge_data.get('object', edge_data.get('entity2', '')).strip()
				confidence = edge_data.get('confidence level', edge_data.get('confidence_level', 0))
				
				if not subject or not object_node:
					continue
				
				# Check if nodes are in id_nodetype_map
				if subject not in id_nodetype_map or object_node not in id_nodetype_map:
					continue
				
				srcType = id_nodetype_map[subject]
				dstType = id_nodetype_map[object_node]
				edgeType = 'EVENT_LLM_SUGGESTED'
				# Use passed default timestamp
				timestamp = default_timestamp
				
				llm_edges.append((subject, srcType, object_node, dstType, edgeType, timestamp))
		
		except Exception as e:
			show(f"Warning: Error processing file {edge_file}: {e}")
			continue
	
	show(f"Successfully parsed {len(llm_edges)} LLM suggested edges")
	return llm_edges

# os.system('tar -zxvf ../graphchi-cpp-master/graph_data/darpatc/ta1-cadets-e3-official.json.tar.gz')
# os.system('tar -zxvf ../graphchi-cpp-master/graph_data/darpatc/ta1-cadets-e3-official-2.json.tar.gz')
# os.system('tar -zxvf ../graphchi-cpp-master/graph_data/darpatc/ta1-fivedirections-e3-official-2.json.tar.gz')
# os.system('tar -zxvf ../graphchi-cpp-master/graph_data/darpatc/ta1-theia-e3-official-1r.json.tar.gz')
# os.system('tar -zxvf ../graphchi-cpp-master/graph_data/darpatc/ta1-theia-e3-official-6r.json.tar.gz')
# os.system('tar -zxvf ../graphchi-cpp-master/graph_data/darpatc/ta1-trace-e3-official-1.json.tar.gz')

# path_list = ['ta1-trace-e3-official-1.json']
path_list = ['ta1-cadets-e3-official.json', 'ta1-cadets-e3-official-2.json']
# path_list = ['ta1-theia-e3-official-1r.json', 'ta1-theia-e3-official-6r.json' , 'ta1-trace-e3-official-1.json']
# path_list = ['ta1-cadets-e3-official.json', 'ta1-cadets-e3-official-2.json', 'ta1-fivedirections-e3-official-2.json', 'ta1-theia-e3-official-1r.json', 'ta1-theia-e3-official-6r.json', 'ta1-trace-e3-official-1.json']

pattern_uuid = re.compile(r'uuid\":\"(.*?)\"') 
pattern_src = re.compile(r'subject\":{\"com.bbn.tc.schema.avro.cdm18.UUID\":\"(.*?)\"}')
pattern_dst1 = re.compile(r'predicateObject\":{\"com.bbn.tc.schema.avro.cdm18.UUID\":\"(.*?)\"}')
pattern_dst2 = re.compile(r'predicateObject2\":{\"com.bbn.tc.schema.avro.cdm18.UUID\":\"(.*?)\"}')
pattern_type = re.compile(r'type\":\"(.*?)\"')
pattern_time = re.compile(r'timestampNanos\":(.*?),')

notice_num = 1000000

# Define shards to process for each file (None means process all shards)
# Format: {filename: [shard index list]}
# Based on last used files, only process required shards
required_shards = {
	'ta1-theia-e3-official-1r.json': [0],           # theia_train: main file(0)
	'ta1-theia-e3-official-6r.json': [8],           # theia_test: shard 8
	'ta1-cadets-e3-official.json': [1],             # cadets_train: shard 1
	'ta1-cadets-e3-official-2.json': [0],            # cadets_test: main file(0)
	'ta1-trace-e3-official-1.json': [0, 4],          # trace: main file(0) and shard 4
}

for path in path_list:
	# Build global node mapping (for parsing LLM edges)
	# Note: To ensure complete LLM edge parsing, still need to scan all shards
	id_nodetype_map = {}
	for i in range(100):
		now_path  = path + '.' + str(i)
		if i == 0: now_path = path
		if not osp.exists(now_path): break
		f = open(now_path, 'r', encoding='utf-8')
		show(f"Building global node mapping: {now_path}")
		cnt  = 0
		for line in f:
			cnt += 1
			if cnt % notice_num == 0:
				print(cnt)
			if 'com.bbn.tc.schema.avro.cdm18.Event' in line or 'com.bbn.tc.schema.avro.cdm18.Host' in line: continue
			if 'com.bbn.tc.schema.avro.cdm18.TimeMarker' in line or 'com.bbn.tc.schema.avro.cdm18.StartMarker' in line: continue
			if 'com.bbn.tc.schema.avro.cdm18.UnitDependency' in line or 'com.bbn.tc.schema.avro.cdm18.EndMarker' in line: continue
			if len(pattern_uuid.findall(line)) == 0: print (line)
			uuid = pattern_uuid.findall(line)[0]
			subject_type = pattern_type.findall(line)

			if len(subject_type) < 1:
				if 'com.bbn.tc.schema.avro.cdm18.MemoryObject' in line:
					id_nodetype_map[uuid] = 'MemoryObject'
					continue
				if 'com.bbn.tc.schema.avro.cdm18.NetFlowObject' in line:
					id_nodetype_map[uuid] = 'NetFlowObject'
					continue
				if 'com.bbn.tc.schema.avro.cdm18.UnnamedPipeObject' in line:
					id_nodetype_map[uuid] = 'UnnamedPipeObject'
					continue

			id_nodetype_map[uuid] = subject_type[0]
		f.close()
	
	# Determine LLM edge directory based on dataset type (before processing shard files)
	dataset_name = None
	path_lower = path.lower()
	if 'trace' in path_lower:
		dataset_name = 'trace_train'
	elif 'theia' in path_lower:
		dataset_name = 'theia_train'
	elif 'cadets' in path_lower:
		dataset_name = 'cadets_train'
	
	# Determine shard list to process (by filename lookup)
	# If shard list is specified, only process those shards; otherwise process all shards
	shards_to_process = None
	if path in required_shards:
		shards_to_process = required_shards[path]
		show(f"File {path} will only process shards: {shards_to_process}")
	
	# Parse all LLM edges (using global node mapping)
	llm_edges_all = []
	if dataset_name:
		script_dir = osp.dirname(osp.abspath(__file__))
		possible_paths = [
			osp.join(script_dir, 'edge', dataset_name),
			osp.join('edge', dataset_name),
			osp.join('scripts', 'edge', dataset_name),
		]
		edge_dir = None
		for p in possible_paths:
			if osp.exists(p):
				edge_dir = p
				break
		
		if edge_dir:
			show(f"Parsing LLM suggested edges for {path} (dataset: {dataset_name}, path: {edge_dir})")
			# First use 0 as default timestamp, later will use earliest timestamp of each shard
			llm_edges_all = parse_llm_edges(edge_dir, id_nodetype_map, '0')
	
	# Process each shard file: extract edges and add LLM edges associated with nodes in this shard
	not_in_cnt = 0
	min_timestamp = None  # Record earliest timestamp for LLM edges
	shard_info = []  # Store information for each shard: (shard index, node mapping, earliest timestamp, edge file path)
	
	for i in range(100):
		# If shard list to process is specified, skip shards not in the list
		if shards_to_process is not None and i not in shards_to_process:
			continue
		now_path  = path + '.' + str(i)
		if i == 0: now_path = path
		if not osp.exists(now_path): break
		
		# Build independent node mapping for current shard
		shard_id_nodetype_map = {}
		f = open(now_path, 'r', encoding='utf-8')
		show(f"Processing shard {i}: {now_path}")
		cnt = 0
		
		# First pass: build node mapping for current shard
		for line in f:
			cnt += 1
			if cnt % notice_num == 0:
				print(cnt)
			if 'com.bbn.tc.schema.avro.cdm18.Event' in line or 'com.bbn.tc.schema.avro.cdm18.Host' in line: continue
			if 'com.bbn.tc.schema.avro.cdm18.TimeMarker' in line or 'com.bbn.tc.schema.avro.cdm18.StartMarker' in line: continue
			if 'com.bbn.tc.schema.avro.cdm18.UnitDependency' in line or 'com.bbn.tc.schema.avro.cdm18.EndMarker' in line: continue
			if len(pattern_uuid.findall(line)) == 0: continue
			uuid = pattern_uuid.findall(line)[0]
			subject_type = pattern_type.findall(line)

			if len(subject_type) < 1:
				if 'com.bbn.tc.schema.avro.cdm18.MemoryObject' in line:
					shard_id_nodetype_map[uuid] = 'MemoryObject'
					continue
				if 'com.bbn.tc.schema.avro.cdm18.NetFlowObject' in line:
					shard_id_nodetype_map[uuid] = 'NetFlowObject'
					continue
				if 'com.bbn.tc.schema.avro.cdm18.UnnamedPipeObject' in line:
					shard_id_nodetype_map[uuid] = 'UnnamedPipeObject'
					continue

			shard_id_nodetype_map[uuid] = subject_type[0]
		f.close()
		
		# Second pass: extract edges and record timestamp
		f = open(now_path, 'r', encoding='utf-8')
		fw = open(now_path+'.edge.txt', 'w', encoding='utf-8')
		shard_min_timestamp = None
		cnt = 0
		for line in f:
			cnt += 1
			if cnt % notice_num == 0:
				print(cnt) 

			if 'com.bbn.tc.schema.avro.cdm18.Event' in line:
				pattern = re.compile(r'subject\":{\"com.bbn.tc.schema.avro.cdm18.UUID\":\"(.*?)\"}')
				edgeType = pattern_type.findall(line)[0]
				timestamp = pattern_time.findall(line)[0]
				# Record earliest timestamp
				try:
					ts_int = int(timestamp)
					if min_timestamp is None or ts_int < min_timestamp:
						min_timestamp = ts_int
					if shard_min_timestamp is None or ts_int < shard_min_timestamp:
						shard_min_timestamp = ts_int
				except:
					pass
				srcId = pattern_src.findall(line)
				if len(srcId) == 0: continue
				srcId = srcId[0]
				if not srcId in id_nodetype_map.keys(): 
					not_in_cnt += 1
					continue
				srcType = id_nodetype_map[srcId]
				dstId1 = pattern_dst1.findall(line)
				if len(dstId1) > 0  and dstId1[0] != 'null':
					dstId1 = dstId1[0]
					if not dstId1 in id_nodetype_map.keys():
						not_in_cnt += 1
						continue
					dstType1 = id_nodetype_map[dstId1]
					this_edge1 = str(srcId) + '\t' + str(srcType) + '\t' + str(dstId1) + '\t' + str(dstType1) + '\t' + str(edgeType) + '\t' + str(timestamp) + '\n'
					fw.write(this_edge1)

				dstId2 = pattern_dst2.findall(line)
				if len(dstId2) > 0  and dstId2[0] != 'null':
					dstId2 = dstId2[0]
					if not dstId2 in id_nodetype_map.keys():
						not_in_cnt += 1
						continue
					dstType2 = id_nodetype_map[dstId2]
					this_edge2 = str(srcId) + '\t' + str(srcType) + '\t' + str(dstId2) + '\t' + str(dstType2) + '\t' + str(edgeType) + '\t' + str(timestamp) + '\n'
					fw.write(this_edge2)	
		fw.close()
		f.close()
		
		# Save shard information for later adding LLM edges
		edge_file_path = now_path + '.edge.txt'
		shard_info.append((i, shard_id_nodetype_map, shard_min_timestamp, edge_file_path))
	
	# Add LLM edges associated with nodes in each shard to each shard file
	if llm_edges_all and shard_info:
		show(f"Starting to add associated LLM edges for each shard of {path}")
		total_added = 0
		for shard_idx, shard_id_nodetype_map, shard_min_timestamp, edge_file_path in shard_info:
			# Filter LLM edges where both source and target nodes are in current shard
			shard_llm_edges = []
			for edge in llm_edges_all:
				srcId, srcType, dstId, dstType, edgeType, timestamp = edge
				# Check if both nodes of the edge are in current shard's node mapping
				if srcId in shard_id_nodetype_map and dstId in shard_id_nodetype_map:
					# Use current shard's earliest timestamp (if exists), otherwise use global earliest timestamp
					edge_timestamp = str(shard_min_timestamp) if shard_min_timestamp is not None else (str(min_timestamp) if min_timestamp is not None else '0')
					shard_llm_edges.append((srcId, srcType, dstId, dstType, edgeType, edge_timestamp))
			
			# Append filtered LLM edges to current shard's edge file
			if shard_llm_edges:
				with open(edge_file_path, 'a', encoding='utf-8') as fw:
					for edge in shard_llm_edges:
						edge_line = '\t'.join(edge) + '\n'
						fw.write(edge_line)
				total_added += len(shard_llm_edges)
				show(f"Shard {shard_idx}: Added {len(shard_llm_edges)} associated LLM edges")
		
		show(f"Total added {total_added} LLM edges for {path} (distributed across shards)")
	elif not llm_edges_all and dataset_name:
		show(f"Warning: LLM edge files not found or edge directory does not exist, skipping adding LLM edges")
	
os.system('cp ta1-theia-e3-official-1r.json.edge.txt ../graphchi-cpp-master/graph_data/darpatc/theia_train_edge.txt')
os.system('cp ta1-theia-e3-official-6r.json.8.edge.txt ../graphchi-cpp-master/graph_data/darpatc/theia_test_edge.txt')
os.system('cp ta1-cadets-e3-official.json.1.edge.txt ../graphchi-cpp-master/graph_data/darpatc/cadets_train_edge.txt')
os.system('cp ta1-cadets-e3-official-2.json.edge.txt ../graphchi-cpp-master/graph_data/darpatc/cadets_test_edge.txt')
os.system('cp ta1-trace-e3-official-1.json.edge.txt ../graphchi-cpp-master/graph_data/darpatc/trace_train_edge.txt')
os.system('cp ta1-trace-e3-official-1.json.4.edge.txt ../graphchi-cpp-master/graph_data/darpatc/trace_test_edge.txt')

# os.system('rm ta1-*')

