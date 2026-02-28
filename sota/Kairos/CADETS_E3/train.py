##########################################################################################
# Some of the code is adapted from:
# https://github.com/pyg-team/pytorch_geometric/blob/master/examples/tgn.py
##########################################################################################

import logging
import numpy as np
from sklearn.utils import class_weight

from kairos_utils import *
from config import *
from model import *

# Setting for logging
logger = logging.getLogger("training_logger")
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler(artifact_dir + 'training.log')
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


def seq_batches(data, batch_size):
    for i in range(0, data.num_events, batch_size):
        src = data.src[i:i + batch_size]
        dst = data.dst[i:i + batch_size]
        t = data.t[i:i + batch_size]
        msg = data.msg[i:i + batch_size]
        yield Batch(src=src, dst=dst, t=t, msg=msg)
 
class Batch:
    def __init__(self, src, dst, t, msg):
        self.src = src
        self.dst = dst
        self.t = t
        self.msg = msg
        self.num_events = len(src)


def train(train_data,
          memory,
          gnn,
          link_pred,
          optimizer,
          neighbor_loader
          ):
    memory.train()
    gnn.train()
    link_pred.train()

    memory.reset_state()  # Start with a fresh memory.
    neighbor_loader.reset_state()  # Start with an empty graph.

    total_loss = 0
    for batch in seq_batches(train_data, batch_size=BATCH):
        optimizer.zero_grad()

        src, pos_dst, t, msg = batch.src, batch.dst, batch.t, batch.msg

        n_id = torch.cat([src, pos_dst]).unique()
        n_id, edge_index, e_id = neighbor_loader(n_id)
        assoc[n_id] = torch.arange(n_id.size(0), device=device)

        # Get updated memory of all nodes involved in the computation.
        z, last_update = memory(n_id)
        z = gnn(z, last_update, edge_index, train_data.t[e_id], train_data.msg[e_id])
        pos_out = link_pred(z[assoc[src]], z[assoc[pos_dst]])

        y_pred = torch.cat([pos_out], dim=0)
        y_true = []
        for m in msg:
            l = tensor_find(m[node_embedding_dim:-node_embedding_dim], 1) - 1
            y_true.append(l)

        y_true = torch.tensor(y_true).to(device=device)
        y_true = y_true.reshape(-1).to(torch.long).to(device=device)

        loss = criterion(y_pred, y_true)

        # Update memory and neighbor loader with ground-truth state.
        memory.update_state(src, pos_dst, t, msg)
        neighbor_loader.insert(src, pos_dst)

        loss.backward()
        optimizer.step()
        memory.detach()
        total_loss += float(loss) * batch.num_events
    return total_loss / train_data.num_events

def load_train_data():
    graph_4_2 = torch.load(graphs_dir + "/graph_4_2.TemporalData.simple").to(device=device)
    graph_4_3 = torch.load(graphs_dir + "/graph_4_3.TemporalData.simple").to(device=device)
    graph_4_4 = torch.load(graphs_dir + "/graph_4_4.TemporalData.simple").to(device=device)
    return [graph_4_2, graph_4_3, graph_4_4]

# # For balanced ONLY
# def collect_all_labels(train_data):
#     """
#     Traverse all training graphs to collect true edge type labels (y_true) for all events.
#     """
#     all_categories = []
    
#     start_idx = node_embedding_dim
    
#     for graph in train_data:
#         graph_msg = graph.msg.to(device)

#         # Extract one-hot encoded labels from the message
#         end_idx = graph_msg.size(-1) - node_embedding_dim
#         one_hot_labels = graph_msg[:, start_idx:end_idx]
#         category_indices = torch.argmax(one_hot_labels, dim=1)

#         all_categories.extend(category_indices.cpu().numpy())
        
#     return np.array(all_categories)

def init_models(node_feat_size):
    memory = TGNMemory(
        max_node_num,
        node_feat_size,
        node_state_dim,
        time_dim,
        message_module=IdentityMessage(node_feat_size, node_state_dim, time_dim),
        aggregator_module=LastAggregator(),
    ).to(device)

    gnn = GraphAttentionEmbedding(
        in_channels=node_state_dim,
        out_channels=edge_dim,
        msg_dim=node_feat_size,
        time_enc=memory.time_enc,
    ).to(device)

    out_channels = len(include_edge_type)
    link_pred = LinkPredictor(in_channels=edge_dim, out_channels=out_channels).to(device)

    optimizer = torch.optim.Adam(
        set(memory.parameters()) | set(gnn.parameters())
        | set(link_pred.parameters()), lr=lr, eps=eps, weight_decay=weight_decay)

    neighbor_loader = LastNeighborLoader(max_node_num, size=neighbor_size, device=device)

    return memory, gnn, link_pred, optimizer, neighbor_loader

if __name__ == "__main__":
    logger.info("Start logging.")

    # Load data for training
    train_data = load_train_data()

# # ----------------------------------
# # For Balanced ONLY
# # ----------------------------------
#     epoch_categories = collect_all_labels(train_data)

#     out_channels = len(include_edge_type) # 7 EVENT types
#     classes_range = np.arange(out_channels)

#     # sklearn for balanced weights
#     class_weights_np = class_weight.compute_class_weight(
#         class_weight="balanced",
#         classes=classes_range,
#         y=epoch_categories,
#     )
    
#     global criterion
#     class_weights = torch.tensor(class_weights_np, dtype=torch.float).to(device=device)
    
#     criterion = torch.nn.CrossEntropyLoss(weight=class_weights) 
    
#     logger.info(f"Initialized Balanced Loss: Weights={class_weights.tolist()}")

    # Initialize the models and the optimizer
    node_feat_size = train_data[0].msg.size(-1)
    memory, gnn, link_pred, optimizer, neighbor_loader = init_models(node_feat_size=node_feat_size)

    # train the model
    for epoch in tqdm(range(1, epoch_num+1)):
        for g in train_data:
            loss = train(
                train_data=g,
                memory=memory,
                gnn=gnn,
                link_pred=link_pred,
                optimizer=optimizer,
                neighbor_loader=neighbor_loader
            )
            logger.info(f'  Epoch: {epoch:02d}, Loss: {loss:.4f}')

    # Save the trained model
    model = [memory, gnn, link_pred, neighbor_loader]

    os.system(f"mkdir -p {models_dir}")
    torch.save(model, f"{models_dir}/models.pt")
