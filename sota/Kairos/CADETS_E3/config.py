########################################################
#
#                   Artifacts path
#
########################################################

# The directory of the raw logs
raw_dir = "/the/absolute/path/of/cadets_e3/"

# The directory to save all artifacts
artifact_dir = "./artifact/"

# The directory to save the vectorized graphs
graphs_dir = artifact_dir + "graphs/"

# The directory to save the models
models_dir = artifact_dir + "models/"

# The directory to save the results after testing
test_re = artifact_dir + "test_re/"

# The directory to save all visualized results
vis_re = artifact_dir + "vis_re/"



########################################################
#
#               Database settings
#
########################################################

# Database name
# database = 'tc_cadet_dataset_db_rcaid'
# database = 'tc_cadet_dataset_db_plugins'
database = 'tc_cadet_dataset_db'

# Only config this setting when you have the problem mentioned
# in the Troubleshooting section in settings/environment-settings.md.
# Otherwise, set it as None
host = '/var/run/postgresql/'
# host = None

# Database user
user = 'postgres'

# The password to the database user
password = 'postgres'

# The port number for Postgres
port = '5432'


########################################################
#
#               Graph semantics
#
########################################################

# The directions of the following edge types need to be reversed
edge_reversed = [
    "EVENT_ACCEPT",
    "EVENT_RECVFROM",
    "EVENT_RECVMSG"
]

# The following edges are the types only considered to construct the
# temporal graph for experiments.
include_edge_type=[
    "EVENT_WRITE",
    "EVENT_READ",
    "EVENT_CLOSE",
    "EVENT_OPEN",
    "EVENT_EXECUTE",
    "EVENT_SENDTO",
    "EVENT_RECVFROM",
    # "EVENT_PSEUDO"  # Added Edges For R-CAID AND PLUGINS
]

# Balanced Weights project to [0.5, 1.5]
# weights_list = [
#     0.5630,  # EVENT_WRITE (0)
#     0.5000,  # EVENT_READ (1)
#     0.5047,  # EVENT_CLOSE (2)
#     0.5050,  # EVENT_OPEN (3)
#     0.6371,  # EVENT_EXECUTE (4)
#     1.4209,  # EVENT_SENDTO (5)
#     1.5000,  # EVENT_RECVFROM (6)
# ]


# Corresponding Weights from plugin2
# weights_list = [
#     0.5000,  # EVENT_WRITE (0)
#     1.5000,  # EVENT_READ (1)
#     1.4773,  # EVENT_CLOSE (2)
#     1.4918,  # EVENT_OPEN (3)
#     1.2062,  # EVENT_EXECUTE (4)
#     0.6777,  # EVENT_SENDTO (5)
#     1.3958,  # EVENT_RECVFROM (6)
#     1.0000,  # EVENT_PSEUDO (7)
# ]

# The map between edge type and edge ID
rel2id = {
 1: 'EVENT_WRITE',
 'EVENT_WRITE': 1,
 2: 'EVENT_READ',
 'EVENT_READ': 2,
 3: 'EVENT_CLOSE',
 'EVENT_CLOSE': 3,
 4: 'EVENT_OPEN',
 'EVENT_OPEN': 4,
 5: 'EVENT_EXECUTE',
 'EVENT_EXECUTE': 5,
 6: 'EVENT_SENDTO',
 'EVENT_SENDTO': 6,
 7: 'EVENT_RECVFROM',
 'EVENT_RECVFROM': 7,
#  8: 'EVENT_PSEUDO',
#  'EVENT_PSEUDO': 8,
}

########################################################
#
#                   Model dimensionality
#
########################################################

# Node Embedding Dimension
node_embedding_dim = 8

# Node State Dimension
node_state_dim = 50

# Neighborhood Sampling Size
neighbor_size = 10

# Edge Embedding Dimension
edge_dim = 50

# The time encoding Dimension
time_dim = 50


########################################################
#
#                   Train&Test
#
########################################################

# Batch size for training and testing
BATCH = 1024

# Parameters for optimizer
lr=0.00005
eps=1e-08
weight_decay=0.01

epoch_num=30

# The size of time window, 60000000000 represent 1 min in nanoseconds.
# The default setting is 15 minutes.
time_window_size = 60000000000 * 15


########################################################
#
#                   Threshold
#
########################################################

beta_day6 = 100
beta_day7 = 100
