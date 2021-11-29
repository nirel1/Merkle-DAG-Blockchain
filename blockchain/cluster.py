import random

from blockchain_utils import BlockchainUtils
from node import Node
from proof_of_stake import ProofOfStake
from pubsub import pub
from wallet import Wallet

import json


class Cluster:

    def __init__(self, c_id=0, t_num=0):
        self.cluster_id = c_id
        self.cluster_topic = str(t_num).strip() + '.c' + str(self.cluster_id).strip()
        self.full_topic = str(t_num).strip() + self.cluster_topic
        self.member_nodes = []
        self.pos = ProofOfStake()
        self.blockchain = None

        pub.subscribe(self.cluster_listener, self.cluster_topic)

    def next_forger(self):
        seed = hash(self)
        next_forger = self.pos.forger(seed)
        return next_forger

    def start_listener(self, cluster_topic):
        pub.subscribe(self.cluster_listener, cluster_topic)

    def cluster_listener(self, arg):
        #print(f'cluster {self.cluster_id} got {arg}')
        t = type(arg)
        if t == Node:
            self.handle_node(arg)

    # publish self to old cluster: handler will see different cluster id and remove from PO
    # publish self to new cluster: handler will see same cluster id and add to POS
    def handle_node(self, node):
        #print(f'cluster {self.cluster_id} is handling node {node}')
        if node not in self.member_nodes:
            # TODO: Need to find issue with proof of stake and reinsert function here.
            if len(self.member_nodes) != 0:
                agg_pub_key = random.choice(self.member_nodes).wallet.public_key_string()
                self.publish([agg_pub_key, node])
            #agg_pub_key = self.next_forger()
            self.member_nodes.append(node)
            # self.publish([agg_pub_key, node])
            self.pos.update(node.wallet.public_key_string(), 10)
        else:
            self.pos.remove_staker(node.wallet.public_key_string())
            self.member_nodes.remove(node)

    def publish(self, message):
        pub.sendMessage(self.cluster_topic, arg=message)

    def to_json(self):
        j_data = {'cluster_id': self.cluster_id,
                'pos': self.pos}
        json_members = []
        for member in self.member_nodes:
            json_members.append(member.to_json())
        j_data['member_nodes'] = json_members
        return j_data
