import psycopg2
from psycopg2.extras import DictCursor, execute_values
import time
from tqdm import tqdm

# ---- Event List (Added EVENT_PSEUDO) ----
include_edge_type = {
    "EVENT_WRITE",
    "EVENT_READ",
    "EVENT_CLOSE",
    "EVENT_OPEN",
    "EVENT_EXECUTE",
    "EVENT_SENDTO",
    "EVENT_RECVFROM",
    "EVENT_PSEUDO",
}


# ---- Init DB connection ----
def get_db():
    conn = psycopg2.connect(
        database="tc_cadet_dataset_db_plugins",
        user="your_name",
        password="your_password",
        host="your_host",
        port="5432",
    )
    return conn, conn.cursor(cursor_factory=DictCursor)


# ---- Loading node2id ----
def load_node_maps(cur):
    uuid2hash = {}
    hash2id = {}

    print("Reading subject_node_table...")
    cur.execute("SELECT node_uuid, hash_id FROM subject_node_table;")
    for row in cur.fetchall():
        uuid2hash[row["node_uuid"]] = row["hash_id"]

    print("Reading file_node_table...")
    cur.execute("SELECT node_uuid, hash_id FROM file_node_table;")
    for row in cur.fetchall():
        uuid2hash[row["node_uuid"]] = row["hash_id"]

    print("Reading netflow_node_table...")
    cur.execute("SELECT node_uuid, hash_id FROM netflow_node_table;")
    for row in cur.fetchall():
        uuid2hash[row["node_uuid"]] = row["hash_id"]

    print("Reading node2id...")
    cur.execute("SELECT hash_id, index_id FROM node2id;")
    for row in cur.fetchall():
        hash2id[row["hash_id"]] = row["index_id"]

    return uuid2hash, hash2id


# ---- Loading edges (Modified for CSV/2-column format) ----
def load_edges(path):
    edges = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            if "," in line:
                parts = line.split(",")
            else:
                parts = line.split()

            if len(parts) >= 2:
                src = parts[0].strip()
                dst = parts[1].strip()
                edges.append((src, dst))
    return edges


# ---- Writing Edges ----
def store_restored_edges(edge_path, batch_size=50000):
    FIXED_TIMESTAMP = 1522641600000000000  # 2018-04-02 00:00:00
    FIXED_EVENT_TYPE = "EVENT_PSEUDO"

    conn, cur = get_db()

    print("Loading node maps...")
    uuid2hash, hash2id = load_node_maps(cur)

    print(f"Loading edges from: {edge_path}")
    edges = load_edges(edge_path)
    print(f"Total edges loaded from file: {len(edges)}")

    insert_rows = []
    count_written = 0

    try:
        # Only src and dst needed
        for uuid_src, uuid_dst in tqdm(edges, desc="Processing edges"):

            if FIXED_EVENT_TYPE not in include_edge_type:
                print(
                    f"Warning: {FIXED_EVENT_TYPE} not in include_edge_type, skipping..."
                )
                break

            if uuid_src not in uuid2hash or uuid_dst not in uuid2hash:
                continue

            src_hash = uuid2hash[uuid_src]
            dst_hash = uuid2hash[uuid_dst]

            # HASH → index_id
            if src_hash not in hash2id or dst_hash not in hash2id:
                continue

            src_id = hash2id[src_hash]
            dst_id = hash2id[dst_hash]

            # construct inserted edge row
            insert_rows.append(
                (src_hash, src_id, FIXED_EVENT_TYPE, dst_hash, dst_id, FIXED_TIMESTAMP)
            )

            if len(insert_rows) >= batch_size:
                execute_values(
                    cur,
                    """
                    INSERT INTO event_table
                    (src_node, src_index_id, operation, dst_node, dst_index_id, timestamp_rec)
                    VALUES %s
                    """,
                    insert_rows,
                )
                conn.commit()
                count_written += len(insert_rows)
                insert_rows = []

        if insert_rows:
            execute_values(
                cur,
                """
                INSERT INTO event_table
                (src_node, src_index_id, operation, dst_node, dst_index_id, timestamp_rec)
                VALUES %s
                """,
                insert_rows,
            )
            conn.commit()
            count_written += len(insert_rows)

        print(f"\nFINISHED! Total edges written: {count_written}")

    except Exception as e:
        conn.rollback()
        print("\nERROR — TRANSACTION ROLLED BACK")
        print(e)

    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    target_file = "./cadets.csv"
    store_restored_edges(target_file, batch_size=2048)
