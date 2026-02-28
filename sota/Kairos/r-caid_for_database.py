import psycopg2
import psycopg2.extras
from tqdm import tqdm
from collections import defaultdict, deque
import config

def init_db():
    """connect to the PostgreSQL database server"""
    print(f"Connecting to database: {config.database}...")
    conn = psycopg2.connect(
        database=config.database,
        user=config.user,
        password=config.password,
        host=config.host,
        port=config.port
    )
    return conn

def load_node_mapping(cur):
    """
    load id2hash mapping from node2id table.
    """
    print("Loading node mapping (index_id -> hash_id)...")
    sql = "SELECT index_id, hash_id FROM node2id"
    cur.execute(sql)
    rows = cur.fetchall()
    
    id2hash = {}
    for r in tqdm(rows, desc="Mapping nodes"):
        id2hash[int(r[0])] = r[1]
    
    return id2hash

def build_graph_and_find_roots(cur):
    """
    1. Build adjacency list from events.
    2. Identify root nodes strictly based on timestamp order.
    """
    print("Fetching events ordered by timestamp to identify Root Nodes...")
    
    # orderd by timestamp_rec ascending
    sql = """
    SELECT src_index_id, dst_index_id 
    FROM event_table 
    ORDER BY timestamp_rec ASC
    """
    
    cur.execute(sql)
    
    adj = defaultdict(list) 
    seen_nodes = set()      
    root_nodes = set()      
    
    while True:
        rows = cur.fetchmany(50000)
        if not rows:
            break
            
        for row in rows:
            try:
                u = int(row[0]) 
                v = int(row[1])
                
                adj[u].append(v)
                
                # === R-CAID Root Finding ===
                
                if u not in seen_nodes:
                    # First time seeing U (Source)
                    root_nodes.add(u)
                    seen_nodes.add(u)
                
                if v not in seen_nodes:
                    seen_nodes.add(v)

            except ValueError:
                continue

    print(f"Graph built. Total Nodes seen: {len(seen_nodes)}")
    print(f"Identified {len(root_nodes)} Root Nodes based on first-timestamp logic.")
    return adj, list(root_nodes)

def find_descendants_and_insert(cur, conn, adj, root_nodes, id2hash):
    """
    for each root node, perform BFS to find all descendants and insert edges.
    """
    print("Processing Root Nodes to find descendants and inserting edges...")
    
    insert_sql = """
    INSERT INTO event_table 
    (src_node, src_index_id, operation, dst_node, dst_index_id, timestamp_rec)
    VALUES %s
    """
    
    batch_data = []
    batch_size = 5000 
    total_new_edges = 0
    
    pbar = tqdm(root_nodes, desc="R-CAID Expansion")
    
    for root_id in pbar:
        # === BFS finding descendants ===
        visited = set()
        queue = deque([root_id])
        descendants = []
        
        visited.add(root_id)
        
        while queue:
            curr = queue.popleft()
            if curr in adj:
                for neighbor in adj[curr]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
                        descendants.append(neighbor)
        
        # === Construct R-CAID Edges ===
        if not descendants:
            continue
            
        root_hash = id2hash.get(root_id)
        if not root_hash: continue

        for desc_id in descendants:
            desc_hash = id2hash.get(desc_id)
            if not desc_hash: continue
            
            # operation: "EVENT_PSEUDO" 
            # timestamp_rec: 1522641600000000000，Mon, 02 Apr 2018 04:00:00 GMT
            row = (
                root_hash, 
                str(root_id), 
                "EVENT_PSEUDO", 
                desc_hash, 
                str(desc_id), 
                1522641600000000000  
            )
            batch_data.append(row)
            total_new_edges += 1
            
            if len(batch_data) >= batch_size:
                psycopg2.extras.execute_values(cur, insert_sql, batch_data)
                conn.commit()
                batch_data = []

    if batch_data:
        psycopg2.extras.execute_values(cur, insert_sql, batch_data)
        conn.commit()
    
    print(f"Finished. Inserted {total_new_edges} new R-CAID dependency edges.")

def main():
    conn = None
    try:
        conn = init_db()
        cur = conn.cursor()
        
        # 1. Load node mapping
        id2hash = load_node_mapping(cur)
        
        # 2. Construct graph and identify root nodes
        # Identified 1006 Root Nodes based on first-timestamp logic.
        adj, root_nodes = build_graph_and_find_roots(cur)
        
        # 3. Find descendants and insert R-CAID edges
        # Inserted 10743804 new R-CAID dependency edges.
        find_descendants_and_insert(cur, conn, adj, root_nodes, id2hash)
        
        print("R-CAID processing complete.")
        
    except Exception as e:
        print(f"Error occurred: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            cur.close()
            conn.close()
            print("Database connection closed.")

if __name__ == "__main__":
    main()