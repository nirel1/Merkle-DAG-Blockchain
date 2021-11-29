## Merkle-DAG Blockchain
This is an implementation of a unique, lightweight blockchain structured using a Directed-Acyclic Graph: intended for recording interactions in Mobile Wireless Sensor Networks. Blocks are organized based on spatiotemporal data. The Merkle-DAG Blockchain is complete with SHA-256 encryption, parent hash validation, signatures, and proof of staking. Several classes are inspired from other codebases, including:
1. PYDAG - Thieman
2. Account_Model, Blockchain_Utils, Transaction - Coursera
3. Interaction, Socket_Communication - P2PNetwork

### Installation
To run the code, a conda environment is needed.

1. Install Anaconda
2. Using the Anaconda Prompt, navigate to the project directory
3. Run the command `conda env create --file environment.yml`
4. Run `conda activate bcenv`
5. Start the code (run manual_test.ipynb, main_notebook.ipynb, or main.py to view performance)

### How it Works
The DAGBlockchain is initialized with a set of dimensions, a genesis-node ID, a genesis-forger, and a cluster ID. The dimensions determine the width of the DAG, as blocks are organized based on their coordinate locations relative to the center of a network. Clusters are used to break a given MWSN into multiple regions, whereby unique blockchains record interactions in their respective areas. We do this because we assume that nodes prioritize interaction with one another by locality. In the test files, a 4x4 grid is used to separate the simulated MWSN into 16 clusters. Each cluster has its own DAGBlockchain, and when clusters collaborate, we observe a merge between two or more blockchains. A node is chosen at initialization from which to generate a genesis block, which acts as the head of the DAG and proves useful for merging/splitting. 

After the genesis block is created, blocks are forged and added using the text files generated from MWSN simulations. Each block is forged upon observing a node at a specific time interval. When this happens, its transactions, node_id, the time, coordinates, forger, parent_hash, and signature are all recorded on the block. The block is then vetted: if the combination of its parameters are unique and its parent can validate the hash, the block will be added using the leaf_selection method in PYDAG -> DAG.

Leaf selection incorporates spatiotemporal data: a new block will select from among available leaves in the blockchain based on its location (subsection) of the cluster. This keeps the DAG growing evenly and permits efficient searches. 
