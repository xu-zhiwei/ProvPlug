#!/usr/bin/env python3
"""
Read edges (src_uuid, dst_uuid) from CSV file and add them to the event_table in the database

Usage:
    python add_edges_from_csv.py <csv_file> [--database DATABASE] [--host HOST] [--port PORT] [--user USER] [--password PASSWORD]

CSV file format:
    src_uuid,dst_uuid
    uuid1,uuid2
    uuid3,uuid4
    ...
"""

import csv
import sys
import uuid
import argparse
import psycopg2
from psycopg2 import extras as ex


def get_uuid_to_node_info(cur):
    """
    Get UUID to (index_id, hash_id) mapping from all node tables
    
    Returns:
        dict: {uuid: (index_id, hash_id)}
    """
    uuid_to_info = {}
    
    # Query all node tables
    queries = {
        "file": "SELECT node_uuid, index_id, hash_id FROM file_node_table;",
        "netflow": "SELECT node_uuid, index_id, hash_id FROM netflow_node_table;",
        "subject": "SELECT node_uuid, index_id, hash_id FROM subject_node_table;",
    }
    
    for _, query in queries.items():
        cur.execute(query)
        rows = cur.fetchall()
        for row in rows:
            node_uuid, index_id, hash_id = row
            uuid_to_info[str(node_uuid)] = (int(index_id), str(hash_id))
    
    return uuid_to_info


def get_reference_values(cur):
    """
    Get reference values from existing edges (most common operation and timestamp range)
    
    Returns:
        tuple: (most_common_operation, avg_timestamp, min_timestamp, max_timestamp)
    """
    # Get the most common operation
    cur.execute("SELECT operation, COUNT(*) as cnt FROM event_table GROUP BY operation ORDER BY cnt DESC LIMIT 1;")
    result = cur.fetchone()
    most_common_operation = result[0] if result else "EVENT_WRITE"  # Default value
    
    # Get timestamp statistics
    cur.execute("SELECT AVG(timestamp_rec), MIN(timestamp_rec), MAX(timestamp_rec) FROM event_table;")
    result = cur.fetchone()
    if result and result[0]:
        avg_timestamp = int(result[0])
        min_timestamp = int(result[1])
        max_timestamp = int(result[2])
    else:
        # If no existing data, use current time (nanoseconds)
        import time
        avg_timestamp = int(time.time() * 1_000_000_000)
        min_timestamp = avg_timestamp - 86400_000_000_000  # 1 day ago
        max_timestamp = avg_timestamp + 86400_000_000_000   # 1 day later
    
    return most_common_operation, avg_timestamp, min_timestamp, max_timestamp


def generate_event_uuid():
    """Generate a new event UUID"""
    return str(uuid.uuid4())


def read_csv_edges(csv_file):
    """
    Read edges from CSV file
    
    Parameters:
        csv_file: Path to CSV file
        
    Returns:
        list: [(src_uuid, dst_uuid), ...]
    """
    edges = []
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            # Skip header row (if present)
            first_row = next(reader, None)
            if first_row and (first_row[0].lower() in ['src_uuid', 'src', 'source'] or 
                             first_row[1].lower() in ['dst_uuid', 'dst', 'destination']):
                pass  # Skip header row
            else:
                # First row is data, need to process
                if len(first_row) >= 2:
                    edges.append((first_row[0].strip(), first_row[1].strip()))
            
            # Read remaining rows
            for row in reader:
                if len(row) >= 2:
                    src_uuid = row[0].strip()
                    dst_uuid = row[1].strip()
                    if src_uuid and dst_uuid:
                        edges.append((src_uuid, dst_uuid))

    except FileNotFoundError:
        print(f"Error: File '{csv_file}' does not exist")
        sys.exit(1)
    except Exception as e:
        print(f"Error: Failed to read CSV file: {e}")
        sys.exit(1)
    
    return edges


def add_edges_to_database(
    csv_file,
    database,
    host=None,
    port=5432,
    user="postgres",
    password="postgres",
    operation=None,
    timestamp=None,
):
    """
    Read edges from CSV file and add them to the database
    
    Parameters:
        csv_file: Path to CSV file
        database: Database name
        host: Database host (None means use default)
        port: Database port
        user: Database username
        password: Database password
        operation: Operation type (if None, get the most common from existing data)
        timestamp: Timestamp (if None, use average timestamp from existing data)
    """
    # Read CSV file
    print(f"Reading CSV file: {csv_file}")
    edges = read_csv_edges(csv_file)
    print(f"Found {len(edges)} edges")
    
    if len(edges) == 0:
        print("Warning: No valid edge data in CSV file")
        return
    
    # Connect to database
    # Auto-detect Docker container environment
    import os
    if host is None:
        # Check environment variable DB_HOST (set by Docker Compose)
        host = os.environ.get('DB_HOST')
        if host:
            print(f"Detected environment variable DB_HOST={host}")
    
    # If still no host, try using 'postgres' (Docker container name)
    if host is None:
        # Check if in container environment (by checking /home/pids path or other container features)
        if os.path.exists('/home/pids') or os.environ.get('COMPOSE_PROJECT_NAME'):
            host = 'postgres'
            print(f"Detected container environment, using default host: {host}")
    
    print(f"Connecting to database: {database}" + (f" (host: {host})" if host else " (local socket)"))
    try:
        if host:
            connect = psycopg2.connect(
                database=database,
                host=host,
                user=user,
                password=password,
                port=port,
            )
        else:
            connect = psycopg2.connect(
                database=database,
                user=user,
                password=password,
                port=port,
            )
        cur = connect.cursor()
    except Exception as e:
        print(f"Error: Failed to connect to database: {e}")
        if host is None:
            print("\nHint: If running in Docker container, use --host postgres parameter")
            print("   Example: python add_edges_from_csv.py file.csv --host postgres")
        sys.exit(1)
    
    # Get UUID to node info mapping
    print("Querying node information...")
    uuid_to_info = get_uuid_to_node_info(cur)
    print(f"Found {len(uuid_to_info)} nodes")
    
    # Get reference values
    print("Getting reference values...")
    ref_operation, ref_avg_timestamp, ref_min_timestamp, ref_max_timestamp = get_reference_values(cur)
    print(f"Most common operation type: {ref_operation}")
    print(f"Timestamp range: {ref_min_timestamp} - {ref_max_timestamp}")
    
    # Use provided values or reference values
    if operation is None:
        operation = ref_operation
    if timestamp is None:
        timestamp = ref_avg_timestamp
    
    # Prepare data for insertion
    print("Preparing data for insertion...")
    datalist = []
    missing_nodes = set()
    
    for src_uuid, dst_uuid in edges:
        # Check if nodes exist
        if src_uuid not in uuid_to_info:
            missing_nodes.add(src_uuid)
            continue
        if dst_uuid not in uuid_to_info:
            missing_nodes.add(dst_uuid)
            continue
        
        # Get node information
        src_index_id, src_hash_id = uuid_to_info[src_uuid]
        dst_index_id, dst_hash_id = uuid_to_info[dst_uuid]
        
        # Generate new event UUID
        event_uuid = generate_event_uuid()
        
        # Prepare data for insertion
        # Format: [src_node, src_index_id, operation, dst_node, dst_index_id, event_uuid, timestamp_rec]
        # Note: src_node and dst_node use hash_id
        datalist.append([
            src_hash_id,      # src_node (hash_id)
            str(src_index_id),  # src_index_id
            operation,        # operation
            dst_hash_id,      # dst_node (hash_id)
            str(dst_index_id),  # dst_index_id
            event_uuid,       # event_uuid
            timestamp,        # timestamp_rec
        ])
    
    # Report missing nodes
    if missing_nodes:
        print(f"\nWarning: The following {len(missing_nodes)} nodes do not exist in the database and will be skipped:")
        for node in list(missing_nodes)[:10]:  # Only show first 10
            print(f"  - {node}")
        if len(missing_nodes) > 10:
            print(f"  ... and {len(missing_nodes) - 10} more nodes")
    
    if len(datalist) == 0:
        print("Error: No valid data to insert")
        connect.close()
        return
    
    # Batch insert data
    print(f"\nInserting {len(datalist)} edges into database...")
    try:
        sql = """INSERT INTO event_table 
                 (src_node, src_index_id, operation, dst_node, dst_index_id, event_uuid, timestamp_rec)
                 VALUES %s"""
        ex.execute_values(cur, sql, datalist, page_size=50000)
        connect.commit()
        print(f"Successfully inserted {len(datalist)} edges")
    except Exception as e:
        connect.rollback()
        print(f"Error: Failed to insert data: {e}")
        sys.exit(1)
    finally:
        cur.close()
        connect.close()


def main():
    parser = argparse.ArgumentParser(
        description="Read edges from CSV file and add them to the event_table in the database"
    )
    parser.add_argument("csv_file", help="Path to CSV file (format: src_uuid,dst_uuid)")
    parser.add_argument("--database", "-d", default="postgres", help="Database name (default: postgres)")
    parser.add_argument("--host", "-H", default=None, help="Database host (default: auto-detect, will use 'postgres' or DB_HOST env var in container)")
    parser.add_argument("--port", "-p", type=int, default=5432, help="Database port (default: 5432)")
    parser.add_argument("--user", "-u", default="postgres", help="Database username (default: postgres)")
    parser.add_argument("--password", "-P", default="postgres", help="Database password (default: postgres)")
    parser.add_argument("--operation", "-o", default=None, help="Operation type (default: get the most common from existing data)")
    parser.add_argument("--timestamp", "-t", type=int, default=None, help="Timestamp (nanoseconds) (default: use average timestamp from existing data)")
    
    args = parser.parse_args()
    
    add_edges_to_database(
        csv_file=args.csv_file,
        database=args.database,
        host=args.host,
        port=args.port,
        user=args.user,
        password=args.password,
        operation=args.operation,
        timestamp=args.timestamp,
    )


if __name__ == "__main__":
    main()