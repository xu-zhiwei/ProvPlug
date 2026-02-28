# PROVPLUG: Extending Velox with LLM-Driven Plugins

This document provides step-by-step guidelines for reproducing Velox enhanced with ProvPlug.

## Introduction & Backgrounds

Velox is a pioneering provenance-based intrusion detection system, originally described in the following publication:

> Tristan Bilot, Baoxiang Jiang, Zefeng Li, Nour El Madhoun, Khaldoun Al Agha, Anis Zouaoui, and Thomas Pasquier. "Sometimes simpler is better: a comprehensive analysis of state-of-the-art provenance-based intrusion detection systems." In *Proceedings of the 34th USENIX Security Symposium (SEC '25)*, USENIX Association, Article 369, pp. 7193–7212, 2025.

This project builds on the open-source Velox codebase, extending its capabilities through ProvPlug. The following sections detail the motivation, integration approach, and implementation steps for reproducing our enhanced system.

## Experimental Design

### Dataset Selection & Exclusion

The original Velox evaluation encompasses three datasets within the DARPA TC E3 collection: THEIA_E3, CADETS_E3, and CLEARSCOPE_E3. However, our reproduction efforts encountered issues with CADETS_E3 and CLEARSCOPE_E3 datasets. Despite extensive efforts to reproduce the baseline performance on these two datasets, we were unable to achieve results same as the original paper. PIDSMaker's codebase continues to be actively maintained, and we are hopeful that future updates will resolve these challenges.

Consequently, after excluding datasets that could not be properly reproduced, we selected **THEIA_E3** as the primary evaluation dataset for Velox enhanced with ProvPlug. 

## Environment Setup

This project uses the original codebase as the basic code framework. PIDSMaker project's github repo has provided a detailed guide on how to setup the running  environment. The readers can refer to this website for basic setup of velox PIDSMaker 
> https://ubc-provenance.github.io/PIDSMaker/ten-minute-install/ 


### Plugin 1

Given the format of CSV files where each line including source node uuid and the destination node uuid. The code file `scripts/plugin1-add-edges-database.py` can be used to add all these edges into the database of the specific dataset (such as THEIA_E3 dataset). 

After the edges being plugged into the database, the Plugin 1 would be ready for evaluation. Just run the pidsmaker velox experiment and all is done. 

To run Plugin 1, simply add the edges into the database and run the velox method : 
```bash
python pidsmaker/main.py velox THEIA_E3  
```

Please consider the README.md and documentation of PIDSMaker codebase for detail on running experiments.



### Plugin 2
In Velox, each edge type is regarded as a substructure and would have a specific weight.

Use the code file `scripts/plugin2-parse-edges-weights.py` to parse the results and get scaled weight for each edge type of Velox method. 

Please consider the code file `PIDSMaker/pidsmaker/objectives/predict_edge_type.py` for the training guidance of Plugin 2.

