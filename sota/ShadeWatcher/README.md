# ProvPlug: Enhancing ShadeWatcher with LLM-Driven Plugins

This project is a reproduction and enhancement of ShadeWatcher, which is introduced by paper:

```
ShadeWatcher: Recommendation-guided Cyber Threat Analysis using System Audit Records
```

## Tech Details

### Dataset preparation
The dataset used is the ta1-trace-e3-official-1.json.4 file from the Darpa TC E3 Trace.

The model requires four files: entity2id.txt, inter2id_o.txt, relation2id.txt, and train2id.txt. However, the open-source code of ShadeWatcher does not generate these four files. Therefore, we wrote build_encoding_from_facts.py in the ./recommend/tools directory to generate these files.

The command to generate the preparatory files is as follows:
```sh
python3 recommend/tools/build_encoding_from_facts.py --dataset trace_4_0.9
```
`trace_4_0.9` is the name of the data folder.

### Increased dataset difficulty
Because reproducing ShadeWatcher resulted in an F1 score of 0.99, to verify the effectiveness of our plugin, we increased the difficulty of the dataset. Specifically, we retained 90% of the nodes in the training set and only kept the edges related to these nodes for training.


## Running

```sh
python ./recommend/driver.py --dataset trace_4_0.9 --epoch 20 --show_val --show_test --gpu_id -1
```


## Results

The result console logs for each experiment are located in the `./results` directory.


