from node import Node
from pubsub import pub
from dag_blockchain import DAGBlockchain
import csv
from copy import deepcopy
from blockchain_utils import BlockchainUtils
import block
from pubsub import pub
from node import Node
from transaction import Transaction
from sensor_transaction import SensorTransaction
from transaction_pool import TransactionPool
from wallet import Wallet
from Crypto.PublicKey import RSA
import pprint
import random
import time
from cluster import Cluster
import copy

import json
import sys
import re
import random

print('start')
nodes = []
clusters = []
clusters2 = []
beginning = time.time()

extra_results = open(f'extra_results.csv', mode='w')

def move_listener(listener, oldtopic, newtopic):
    pub.unsubscribe(listener, oldtopic)  
    pub.subscribe(listener, newtopic)


def create_clusters(new_nodes):
    beg2 = time.time()
    for j in range(16):
        new_cluster = Cluster(j + 1, 0)
        genesis_node_id = j + 1
        new_genesis_forger = new_nodes[j].wallet.public_key_string()
        dag_blockchain = DAGBlockchain(4, genesis_node_id, new_genesis_forger)
        new_cluster.blockchain = dag_blockchain
        clusters.append(new_cluster)
    print(f'time to initialize {len(clusters)} clusters: {time.time() - beg2}')

def create_clusters2(new_nodes):
    for j in range(16):
        new_cluster = Cluster(j + 1, 0)
        genesis_node_id = j + 1
        new_genesis_forger = new_nodes[j].wallet.public_key_string()
        dag_blockchain = DAGBlockchain(1, genesis_node_id, new_genesis_forger)
        new_cluster.blockchain = dag_blockchain
        clusters2.append(new_cluster)

with open('./extra_data.txt') as f:
    lines = f.readlines()  # list containing lines of file
    i = 0
    for line in lines:
        parts = line.split(',')
        if i < 80:
            new_node = Node(0, i + 1, int(parts[5].strip()))
            new_node.coords = [float(parts[2].strip()), float(parts[3].strip())]
            nodes.append(new_node)
        else:
            if i == 80:
                create_clusters(nodes)
                create_clusters2(nodes)
                beg3 = time.time()
            cur_node = nodes[i % 80]
            cur_node.coords = [float(parts[2].strip()), float(parts[3].strip())]
            cur_node.cluster_id = int(parts[5].strip())

            # time to create block and add to DAG blockchain
            timer = time.time()
            genesis_forger = clusters[cur_node.cluster_id - 1].blockchain.genesis_forger
            new_block = block.Block([], i, int(cur_node.coords[0]),
                                    int(cur_node.coords[1]), genesis_forger)
            new_block.cluster_id = cur_node.cluster_id
            # time to add to add
            dag_start = time.time()
            clusters[cur_node.cluster_id - 1].blockchain.add_block(new_block)
            dag_end = time.time() - dag_start
            block_end = time.time() - timer

            # time to add to linked list
            control_start = time.time()
            clusters2[cur_node.cluster_id - 1].blockchain.add_block(new_block)
            control_end = time.time() - control_start
            
            extra_blockchain = deepcopy(clusters[0].blockchain)
            extra_blockchain2 = deepcopy(clusters[cur_node.cluster_id - 1].blockchain)
            merge_start = time.time()
            extra_blockchain.merge(extra_blockchain2)
            merge_end = time.time() - merge_start

            branch_size_writer = csv.writer(extra_results, delimiter=',', quotechar='"',
                                            quoting=csv.QUOTE_MINIMAL)
            branch_size_writer.writerow([i, cur_node.cluster_id,
                                         clusters[cur_node.cluster_id - 1].blockchain.size, block_end, dag_end, control_end,
                                         merge_end])
        i += 1

    beg4 = time.time()
    for k in range(14):
        clusters[0].blockchain.merge(clusters[k+1].blockchain)

    print(f'time to merge all cluster blockchains: {time.time() - beg4}')
    clusters[0].blockchain.visualize('merged_graph.png')
