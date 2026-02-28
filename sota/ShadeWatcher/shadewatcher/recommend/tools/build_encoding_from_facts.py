import os, argparse, glob, json, subprocess, tempfile, random

REL_NAMES = [
    "vfork","clone","execve","kill","pipe","delete","create","recv","send",
    "mkdir","rmdir","open","load","read","write","connect","getpeername",
    "filepath","mode","mtime","linknum","uid","count","nametype","version","dev","sizebyte"
]

def read_node_ids(nodefact_path):
    with open(nodefact_path, 'r') as f:
        n = int(f.readline().strip())
        ids = []
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 1:
                ids.append(int(parts[0]))
        if n != len(ids):
            n = len(ids)
        hash2id = {h:i for i, h in enumerate(ids)}
    return hash2id, n

def write_entity2id(out_dir, hash2id, n):
    path = os.path.join(out_dir, 'entity2id.txt')
    with open(path, 'w') as f:
        f.write(str(n) + "\n")
        for h, i in hash2id.items():
            f.write(f"{h} {i}\n")

def write_relation2id(out_dir):
    path = os.path.join(out_dir, 'relation2id.txt')
    with open(path, 'w') as f:
        f.write(str(len(REL_NAMES)) + "\n")
        for i, name in enumerate(REL_NAMES):
            f.write(f"{name} {i}\n")

def collect_triples(out_dir, hash2id):
    triples = []
    edge_files = sorted(glob.glob(os.path.join(out_dir, 'edgefact_*.txt')))
    for ef in edge_files:
        with open(ef, 'r') as f:
            try:
                _count = int(f.readline().strip())
            except:
                pass
            for line in f:
                parts = line.strip().split()
                if len(parts) < 4:
                    continue
                n1 = int(parts[1]); n2 = int(parts[2]); rel = int(parts[3]) - 1
                if n1 in hash2id and n2 in hash2id and 0 <= rel < len(REL_NAMES):
                    triples.append((hash2id[n1], hash2id[n2], rel))
    return triples

def write_train2id(out_dir, triples, mal_ids):
    path = os.path.join(out_dir, 'train2id.txt')
    with open(path, 'w') as f:
        valid_triples = []
        for h, t, r in triples:
            if h in mal_ids and t in mal_ids:
                continue
            valid_triples.append((h, t, r))
        f.write(str(len(valid_triples)) + "\n")
        for h, t, r in valid_triples:
            f.write(f"{h} {t} {r}\n")

def write_inter2id(out_dir, triples):
    neigh = {}
    for h, t, _ in triples:
        neigh.setdefault(h, set()).add(t)
        neigh.setdefault(t, set()).add(h)
    path = os.path.join(out_dir, 'inter2id_0.txt')
    with open(path, 'w') as f:
        for e, ns in neigh.items():
            if ns:
                f.write(str(e) + " " + " ".join(str(x) for x in ns) + "\n")
    return neigh

def write_inter2id_split(out_dir, neigh, mal_ids):
    be_path = os.path.join(out_dir, 'inter2id_be.txt')
    me_path = os.path.join(out_dir, 'inter2id_me.txt')
    with open(be_path, 'w') as f_be, open(me_path, 'w') as f_me:
        for e, ns in neigh.items():
            be_ns = [x for x in ns if not (e in mal_ids and x in mal_ids)]
            me_ns = [x for x in ns if e in mal_ids and x in mal_ids]
            if be_ns:
                f_be.write(str(e) + " " + " ".join(str(x) for x in be_ns) + "\n")
            if me_ns:
                f_me.write(str(e) + " " + " ".join(str(x) for x in me_ns) + "\n")


def read_inter2id_file(path):
    neigh = {}
    if not os.path.exists(path):
        return neigh
    with open(path, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if not parts:
                continue
            e = int(parts[0])
            ns = [int(x) for x in parts[1:]]
            neigh[e] = set(ns)
    return neigh


def write_inter2id_be_subset(out_dir, keep_ratio=0.9, seed=42):
    be_path = os.path.join(out_dir, 'inter2id_be.txt')
    neigh_be = read_inter2id_file(be_path)
    nodes = list(neigh_be.keys())
    if not nodes:
        return set()

    rnd = random.Random(seed)
    rnd.shuffle(nodes)

    k80 = int(len(nodes) * 0.9)
    if k80 <= 0:
        k80 = 1
    nodes_80 = set(nodes[:k80])
    nodes_20 = set(nodes[k80:])

    be80_path = os.path.join(out_dir, 'inter2id_be_80.txt')
    be20_path = os.path.join(out_dir, 'inter2id_be_20.txt')
    with open(be80_path, 'w') as f80, open(be20_path, 'w') as f20:
        for e in sorted(neigh_be.keys()):
            ns = sorted(neigh_be[e])
            if not ns:
                continue
            line = str(e) + " " + " ".join(str(x) for x in ns) + "\n"
            if e in nodes_80:
                f80.write(line)
            else:
                f20.write(line)

    nodes80_list = list(nodes_80)
    if not nodes80_list:
        return set()
    k_keep = int(len(nodes80_list) * keep_ratio)
    if k_keep <= 0:
        k_keep = 1
    kept = set(rnd.sample(nodes80_list, k_keep))

    sub_path = os.path.join(out_dir, 'inter2id_be_80_0.9.txt')
    with open(sub_path, 'w') as f:
        for e in sorted(neigh_be.keys()):
            if e not in kept:
                continue
            ns = [n for n in neigh_be[e] if n in kept and n in nodes_80]
            if ns:
                f.write(str(e) + " " + " ".join(str(x) for x in ns) + "\n")
    return kept


def write_train2id_subset(out_dir, triples, mal_ids, kept_nodes):
    path = os.path.join(out_dir, 'train2id2_2_0.9.txt')
    valid_triples = []
    for h, t, r in triples:
        if h not in kept_nodes or t not in kept_nodes:
            continue
        if h in mal_ids and t in mal_ids:
            continue
        valid_triples.append((h, t, r))
    with open(path, 'w') as f:
        f.write(str(len(valid_triples)) + "\n")
        for h, t, r in valid_triples:
            f.write(f"{h} {t} {r}\n")

def ensure_attr_file(out_dir):
    path = os.path.join(out_dir, 'attr2id.txt')
    if not os.path.exists(path):
        with open(path, 'w') as f:
            f.write("0\n")

def _ensure_hash_bin():
    bin_path = "/tmp/hashstr"
    if os.path.exists(bin_path):
        return bin_path
    code = r'''
    #include <iostream>
    #include <string>
    #include <functional>
    int main(){
        std::string s;
        std::hash<std::string> h;
        while(std::getline(std::cin, s)){
            if(s.empty()) continue;
            long long v = (long long)h(s);
            std::cout << v << "\n";
        }
        return 0;
    }
    '''
    fd, cpp_path = tempfile.mkstemp(suffix=".cpp")
    os.write(fd, code.encode("utf-8"))
    os.close(fd)
    try:
        subprocess.run(["g++", "-O2", "-std=c++17", cpp_path, "-o", bin_path], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    finally:
        try:
            os.remove(cpp_path)
        except:
            pass
    return bin_path

def _hash_strings_to_ids(strings):
    bin_path = _ensure_hash_bin()
    inp = "\n".join([s for s in strings if s]).encode("utf-8")
    p = subprocess.run([bin_path], input=inp, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    lines = p.stdout.decode("utf-8").strip().splitlines()
    ids = []
    for ln in lines:
        try:
            ids.append(int(ln.strip()))
        except:
            continue
    return ids

def read_malicious_ids_from_trace(trace_path, hash2id):
    if not os.path.exists(trace_path):
        return set()
    with open(trace_path, 'r') as f:
        trace_ids = json.load(f)
    hashed = _hash_strings_to_ids(trace_ids)
    mal_ids = set()
    for h in hashed:
        if h in hash2id:
            mal_ids.add(hash2id[h])
    return mal_ids

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dataset', required=True)
    args = ap.parse_args()
    out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'encoding', args.dataset))
    nodefact = os.path.join(out_dir, 'nodefact.txt')
    if not os.path.exists(nodefact):
        raise FileNotFoundError(f"not found: {nodefact}")
    hash2id, n = read_node_ids(nodefact)
    write_entity2id(out_dir, hash2id, n)
    write_relation2id(out_dir)
    triples = collect_triples(out_dir, hash2id)
    ensure_attr_file(out_dir)
    trace_path = os.path.abspath(os.path.join(os.path.expanduser('~'), 'Flash-IDS-main', 'data_files', 'trace.json'))
    mal_ids = read_malicious_ids_from_trace(trace_path, hash2id)
    neigh = write_inter2id(out_dir, triples)
    write_inter2id_split(out_dir, neigh, mal_ids)
    kept_nodes = write_inter2id_be_subset(out_dir, keep_ratio=0.9, seed=42)
    write_train2id_subset(out_dir, triples, mal_ids, kept_nodes)
    print(f"done. files in {out_dir}: entity2id.txt, relation2id.txt, train2id2_2_0.9.txt, inter2id_0.txt, inter2id_be.txt, inter2id_be_80.txt, inter2id_be_20.txt, inter2id_be_80_0.9.txt, inter2id_me.txt, attr2id.txt")

if __name__ == '__main__':
    main()
