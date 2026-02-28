# ProvPlug: Enhancing ThreaTrace with LLM-Driven Plugins

This guide provides comprehensive documentation for ThreaTrace.


## Docker Usage

### Prerequisites

- Docker installed (version 20.10 or higher)
- NVIDIA Docker runtime (nvidia-docker2) for GPU support
- NVIDIA GPU with CUDA 11.1+ support (optional, for GPU acceleration)

### Building the Docker Image

Build the Docker image from the project root directory:

```bash
cd /path/to/threaTrace
docker build -t threatrace:latest -f Dockerfile .
```

The Dockerfile includes:
- **Base Image**: `nvidia/cuda:11.1.1-devel-ubuntu20.04`
- **Python**: 3.6.13 (Conda environment: `threatrace`)
- **PyTorch**: 1.9.1 + cu111
- **Torch Geometric**: 1.4.3 + cu111
- **Other Dependencies**: numpy, pandas, scikit-learn, etc.

### Running Docker Container

#### Basic Usage (CPU)

```bash
docker run -it --rm \
  -v $(pwd):/threaTrace \
  -w /threaTrace \
  threatrace:latest \
  bash
```

#### GPU Support

For GPU acceleration, use `--gpus all`:

```bash
docker run -it --rm \
  --gpus all \
  -v $(pwd):/threaTrace \
  -w /threaTrace \
  threatrace:latest \
  bash
```

#### With Data Volume Mount

If your data is in a separate directory:

```bash
docker run -it --rm \
  --gpus all \
  -v $(pwd):/threaTrace \
  -v /path/to/data:/data \
  -w /threaTrace \
  threatrace:latest \
  bash
```

### Activating Conda Environment

Once inside the container, activate the conda environment:

```bash
conda activate threatrace
```

Or it will be automatically activated if you use the bashrc:

```bash
source ~/.bashrc
```

### Running DARPA Scripts in Docker

#### Data Parsing

```bash
# Inside Docker container
cd /threaTrace/scripts
python parse_darpatc.py
```

#### Training

```bash
# Inside Docker container
cd /threaTrace/scripts
python train_darpatc.py --scene theia --model SAGE
```

#### Testing

```bash
# Inside Docker container
cd /threaTrace/scripts
python test_darpatc.py --scene theia --model 0
```

#### Evaluation

```bash
# Inside Docker container
cd /threaTrace/scripts
python evaluate_darpatc.py
```

### Docker Compose (Optional)

Create a `docker-compose.yml` file for easier management:

```yaml
version: '3.8'

services:
  threatrace:
    build:
      context: .
      dockerfile: Dockerfile
    image: threatrace:latest
    container_name: threatrace
    volumes:
      - .:/threaTrace
      - ./data:/data
    working_dir: /threaTrace
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    stdin_open: true
    tty: true
    command: bash
```

Then run:

```bash
docker-compose up -d
docker-compose exec threatrace bash
```

### Complete Docker Workflow Example

```bash
# 1. Build the image
docker build -t threatrace:latest -f Dockerfile .

# 2. Run container with GPU support
docker run -it --rm \
  --gpus all \
  -v $(pwd):/threaTrace \
  -w /threaTrace \
  threatrace:latest \
  bash

# 3. Inside container: activate environment
conda activate threatrace

# 4. Parse DARPA data
cd scripts
python parse_darpatc.py

# 5. Train model
python train_darpatc.py --scene theia --model SAGE

# 6. Test model
python test_darpatc.py --scene theia --model 0

# 7. Evaluate results
python evaluate_darpatc.py
```

### Docker Tips

1. **Persistent Data**: Mount volumes to persist data and models outside the container
   ```bash
   -v $(pwd)/models:/threaTrace/models
   -v $(pwd)/graphchi-cpp-master/graph_data:/threaTrace/graphchi-cpp-master/graph_data
   ```

2. **Resource Limits**: Set memory and CPU limits if needed
   ```bash
   --memory="8g" --cpus="4"
   ```

3. **Background Execution**: Run commands in detached mode
   ```bash
   docker run -d --name threatrace-training \
     --gpus all \
     -v $(pwd):/threaTrace \
     threatrace:latest \
     bash -c "cd /threaTrace/scripts && conda activate threatrace && python train_darpatc.py --scene theia"
   ```

4. **View Logs**: Check container logs
   ```bash
   docker logs threatrace-training
   ```

5. **Interactive Debugging**: Attach to running container
   ```bash
   docker exec -it threatrace-training bash
   ```

### Troubleshooting Docker Issues

1. **GPU Not Available**
   - Ensure nvidia-docker2 is installed
   - Check GPU visibility: `nvidia-smi`
   - Verify CUDA version compatibility

2. **Permission Errors**
   - Use `--user $(id -u):$(id -g)` to match host user
   - Or fix permissions on mounted volumes

3. **Out of Memory**
   - Reduce batch size in training scripts
   - Increase Docker memory limit
   - Use CPU-only mode if GPU memory is insufficient

4. **Conda Environment Not Found**
   - Ensure you're using the correct shell: `bash -lc`
   - Manually activate: `conda activate threatrace`




## Data Parsing

### Basic Parsing

**`parse_darpatc.py`**
- Parses raw DARPA JSON files into edge list format
- Extracts nodes and edges from CDM18 format
- Output: Edge files in format `srcId \t srcType \t dstId \t dstType \t edgeType \t timestamp`
- Usage:
  ```bash
  python parse_darpatc.py
  ```
- Configuration: Edit `path_list` to specify which datasets to process

**`parse_darpatc_better.py`**
- Improved version with better error handling and node type extraction
- More robust parsing logic

### Edge Enhancement Parsing

**`parse_darpatc_edge.py`**
- Parses DARPA data and adds LLM-suggested edges
- Reads LLM edge suggestions from `scripts/edge/{dataset}_train/` directories
- Supports multiple edge file formats (JSON arrays or objects)
- Usage:
  ```bash
  python parse_darpatc_edge.py
  ```
- Configuration:
  - Edit `path_list` to specify datasets
  - Edit `required_shards` to specify which shards to process
  - LLM edge files should be in format: `{dataset}_train_result_*.txt


## Training

### Basic Training

**`train_darpatc.py`**
- Standard training script for DARPA datasets
- Uses SAGEConv with hidden dimension 32
- Implements iterative training with validation
- Usage:
  ```bash
  python train_darpatc.py --scene theia --model SAGE
  ```
- Arguments:
  - `--scene`: Dataset name (cadets, trace, theia, fivedirections)
  - `--model`: Model type (currently only SAGE)
- Output:
  - Model checkpoints: `../models/model_{loop_num}`
  - False positive/negative features: `../models/{fp|tn}_feature_label_{graphId}_{loop_num}.txt`

### Edge-Enhanced Training

**`train_darpatc_edge.py`**
- Training with LLM-suggested edges
- Uses data processed by `parse_darpatc_edge.py`
- Same usage as `train_darpatc.py`


### Data Processing for Training

**`data_process_train.py`**
- Processes training data into PyTorch Geometric format
- Creates node features, labels, and edge indices
- Basic version without weight support


## Testing

### Basic Testing

**`test_darpatc.py`**
- Tests trained models on test datasets
- Uses threshold-based prediction
- Usage:
  ```bash
  python test_darpatc.py --scene theia --model 0
  ```
- Arguments:
  - `--scene`: Dataset name
  - `--model`: Model checkpoint number to use
- Output:
  - `alarm.txt`: Predicted anomalies with neighbor information

### Edge-Enhanced Testing

**`test_darpatc_edge.py`**
- Testing with LLM-suggested edges
- Same usage as `test_darpatc.py`

### Data Processing for Testing

**`data_process_test.py`**
- Processes test data into PyTorch Geometric format
- Includes ground truth node mapping
- Basic version without weight support

## Evaluation

**`evaluate_darpatc.py`**
- Evaluates test results against ground truth
- Calculates precision, recall, F1-score, and other metrics
- Usage:
  ```bash
  python evaluate_darpatc.py
  ```
- Input:
  - `groundtruth_nodeId.txt`: Ground truth node IDs
  - `alarm.txt`: Predicted anomalies
  - `id_to_uuid.txt`: Node ID to UUID mapping
- Output:
  - Precision, Recall, F1-score
  - True Positive (TP), False Positive (FP), True Negative (TN), False Negative (FN) counts


## Complete Workflow

### Using Docker (Recommended)

For a consistent environment, use Docker:

```bash
# 1. Build Docker image
docker build -t threatrace:latest -f Dockerfile .

# 2. Run container with GPU support
docker run -it --rm \
  --gpus all \
  -v $(pwd):/threaTrace \
  -w /threaTrace \
  threatrace:latest \
  bash

# 3. Inside container: activate environment and run workflow
conda activate threatrace
cd scripts

# Parse data
python parse_darpatc.py

# Train model
python train_darpatc.py --scene theia --model SAGE

# Test model
python test_darpatc.py --scene theia --model 0

# Evaluate results
python evaluate_darpatc.py
```

### Standard Workflow (Local Installation)

1. **Parse Raw Data**
   ```bash
   python parse_darpatc.py
   ```
   - Output: `{dataset}_{train|test}.txt` in `../graphchi-cpp-master/graph_data/darpatc/`

2. **Train Model**
   ```bash
   python train_darpatc.py --scene theia --model SAGE
   ```
   - Output: Model checkpoints in `../models/`

3. **Test Model**
   ```bash
   python test_darpatc.py --scene theia --model 0
   ```
   - Output: `alarm.txt` with predictions

4. **Evaluate Results**
   ```bash
   python evaluate_darpatc.py
   ```
   - Output: Precision, Recall, F1-score

### Enhanced Workflow with LLM Edges

1. **Parse Data with LLM Edges**
   ```bash
   python parse_darpatc_edge.py
   ```
   - Ensure LLM edge files are in `scripts/edge/{dataset}_train/`
   - Output: `{dataset}_{train|test}_edge.txt`

2. **Train with Enhanced Data**
   ```bash
   python train_darpatc_edge.py --scene theia --model SAGE
   ```

3. **Test with Enhanced Data**
   ```bash
   python test_darpatc_edge.py --scene theia --model 0
   ```

## Configuration

### Dataset Names
- `cadets`: CADETS dataset
- `trace`: TRACE dataset
- `theia`: THEIA dataset

### Thresholds
Default thresholds for different datasets:
- `cadets`: 1.5
- `trace`: 1.0
- `theia`: 1.5

### Model Architecture
- **Standard**: SAGEConv with hidden dimension 32
- **Balanced Weights**: SAGEConv with hidden dimension 8
- **Layers**: 2 (conv1: in_channels → hidden, conv2: hidden → out_channels)
- **Activation**: ReLU
- **Dropout**: 0.5
- **Optimizer**: Adam (lr=0.01, weight_decay=5e-4)

## References

- DARPA TC (Transparent Computing) Program
- CDM18 (Common Data Model v18) Format
- PyTorch Geometric Documentation
- Graph Neural Networks for Threat Detection

