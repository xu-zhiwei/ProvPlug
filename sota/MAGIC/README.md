# ProvPlug: Enhancing MAGIC with LLM-Driven Plugins

This project is a reproduction and enhancement of **MAGIC**, a state-of-the-art provenance graph-based intrusion detection system. 


> **MAGIC: Detecting Advanced Persistent Threats via Masked Graph Representation Learning**  
> Zian Jia, Yun Xiong, Yuhong Nan, Yao Zhang, Jinjing Zhao, Mi Wen  
> *2024 USENIX Security Symposium (Security)*  
> 📄 [Paper](https://www.usenix.org/system/files/sec23winter-prepub-490-jia.pdf) | 💻 [Official Repository](https://github.com/FDUDSDE/MAGIC)


## Dependencies

- Python 3.8
- PyTorch 1.12.1
- DGL 1.0.0
- Scikit-learn 1.2.2

Please install the required Python packages using the following command:
```bash
pip install -r requirements.txt
```

## Results Reproduction

We release the results achieved by ProvPlug-enhanced MAGIC in the `results/` directory. It includes:

- `results/Plugin1/`: Results from MAGIC enhanced with Plugin 1.
- `results/Plugin2/`: Results from MAGIC enhanced with Plugin 2.
- `results/Plugin1+2/`: Results from MAGIC enhanced with both Plugin 1 and Plugin 2.

Both checkpoints and console logs are provided for reference.