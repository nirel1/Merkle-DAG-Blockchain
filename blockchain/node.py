from sensor_transaction import SensorTransaction
from wallet import Wallet
from message import Message
from block import Block
from blockchain_utils import BlockchainUtils
from pubsub import pub
from transaction_pool import TransactionPool

import copy
import csv
import time


# from socket_communication import SocketCommunication
# from node_api import NodeAPI


class Node:

    def __init__(self, test_num, node_id, cluster_id, blockchain=None, key=None):
        self.test_num = test_num
        self.node_id = node_id
        self.cluster_id = cluster_id
        # self.port = port
        self.blockchain = blockchain
        self.blockchain_size = 1
        self.transaction_pool = TransactionPool()
        self.wallet = Wallet()
        self.coords = [0.0, 0.0]
        if key is not None:
            self.wallet.from_key(key)

    # def startP2P(self):
    #     self.p2p = SocketCommunication(self.ip, self.port)
    #     self.p2p.startSocketCommunication(self)

    # def startAPI(self, apiPort):
    #     self.api = NodeAPI()
    #     self.api.injectNode(self)
    #     self.api.start(apiPort)

    def start_listener(self, cluster_topic):
        pub.subscribe(self.node_listener, cluster_topic)

    def node_listener(self, arg):
        t = type(arg)
        if t is Block:
            # print(f'n{self.node_id} in c{self.cluster_id} received Block: {arg}')
            self.handle_block(arg)
        elif t is MKDBlockchain:
            # print(f'n{self.node_id} in c{self.cluster_id} received MKDBlockchain: {arg}')
            self.handle_blockchain(arg)
        elif t is SensorTransaction:
            # print(f'n{self.node_id} in c{self.cluster_id} received SensorTransaction: {arg}')
            self.handle_sensor_transaction(arg)
        elif t is list:
            # print(f'n{self.node_id} in c{self.cluster_id} received list: {arg}')
            self.handle_aggregator(arg)

    def move_listener(self, old_topic, new_topic):
        pub.unsubscribe(self.node_listener, old_topic)  # core.TopicManager.getTopicsSubscribed(listener))
        pub.subscribe(self.node_listener, new_topic)

    def publish(self, message):
        cluster = self.cluster_id
        pub.sendMessage(cluster, arg=message)

    # TODO: Verify function of handle_sensor_transaction
    def handle_sensor_transaction(self, sensor_transaction):
        data = sensor_transaction.payload()
        signature = sensor_transaction.signature
        signer_public_key = sensor_transaction.sender_public_key
        signature_valid = Wallet.signature_valid(
            data, signature, signer_public_key)
        transaction_exists = self.transaction_pool.transaction_exists(sensor_transaction)
        transaction_in_block = self.blockchain.transaction_exists(sensor_transaction)
        if not transaction_exists and not transaction_in_block and signature_valid:
            self.transaction_pool.add_transaction(sensor_transaction)

    def handle_transaction(self, transaction):
        data = transaction.payload()
        signature = transaction.signature
        signer_public_key = transaction.sender_public_key
        signature_valid = Wallet.signature_valid(
            data, signature, signer_public_key)
        transaction_exists = self.transaction_pool.transaction_exists(transaction)
        transaction_in_block = self.blockchain.transaction_exists(transaction)
        if not transaction_exists and not transaction_in_block and signature_valid:
            self.transaction_pool.add_transaction(transaction)
            message = Message(self.p2p.socketConnector,
                              'TRANSACTION', transaction)
            encoded_message = BlockchainUtils.encode(message)
            self.p2p.broadcast(encoded_message)
            forging_required = self.transaction_pool.forging_required()
            if forging_required:
                self.forge()

    def handle_block(self, block):
        self.blockchain.blocks.add(block)
        self.blockchain_size += 1
        self.transaction_pool.remove_from_pool(block.transactions)
        # for transaction in block.transactions:
        #     if self.transaction_pool.transaction_exists(transaction):
        #         self.transaction_pool.remove_from_pool(transaction)

        # forger = block.forger
        # block_hash = block.payload()d
        # signature = block.signature
        # block_count_valid = self.blockchain.block_count_valid(block)
        # parent_block_hash_valid = self.blockchain.parent_block_hash_valid(block)
        # forger_valid = self.blockchain.forger_valid(block)
        # transactions_valid = self.blockchain.transactions_valid(
            # block.transactions)
        # signature_valid = Wallet.signature_valid(block_hash, signature, forger)
        # if not block_count_valid:
        #     self.blockchain.request_chain()
        # if last_block_hash_valid and forger_valid and transactions_valid and signature_valid:
        #     self.blockchain.add_block(block)
        #     self.transaction_pool.remove_from_pool(block.transactions)
        #     message = Message(self.p2p.socketConnector, 'BLOCK', block)
        #     self.p2p.broadcast(BlockchainUtils.encode(message))

    def handle_blockchain_request(self, requesting_node):
        message = Message(self.p2p.socketConnector,
                          'BLOCKCHAIN', self.blockchain)
        self.p2p.send(requesting_node, BlockchainUtils.encode(message))

    # TODO: Need to add functionality for when blockchain is broadcast after merge and confirm function of deepcopy
    def handle_blockchain(self, blockchain):
        if len(blockchain.blocks) == 1:
            self.blockchain = copy.deepcopy(blockchain)
            self.blockchain.chain_id = self.cluster_id
        else:
            self.blockchain.blocks.merge(blockchain.blocks, self.blockchain.blocks)
            self.blockchain.pos = copy.deepcopy(blockchain.pos)
            pub.sendMessage()
        """for block in blockchain.blocks.inorder():
                    print(block)
                local_blockchain_copy = copy.deepcopy(self.blockchain)
                print(local_blockchain_copy)
                if local_blockchain_copy is not None:
                    local_block_count = len(local_blockchain_copy.blocks)
                else:
                    local_block_count = 0
                received_chain_block_count = len(blockchain.blocks)
                if local_block_count < received_chain_block_count:
                    for block_number, block in enumerate(blockchain.blocks):
                        if block_number >= local_block_count:
                            local_blockchain_copy.add_block(block)
                            self.transaction_pool.remove_from_pool(block.transactions)
                    self.blockchain = local_blockchain_copy"""

    def handle_aggregator(self, arg):
        agg_pub_key = arg[0]
        if agg_pub_key != self.wallet.public_key_string():
            return

        node_to_aggregate = arg[1]  # node received
        first_tree = self.blockchain.blocks
        second_tree = node_to_aggregate.blockchain.blocks
        #  TODO: Add functionality for merging tree based on different factors such as size, etc.
        merged_into_tree = first_tree  # if first_tree.size > second_tree.size else second_tree
        merging_tree = second_tree  # first_tree if merged_into_tree != first_tree else second_tree

        merged_into_tree_size = len(merged_into_tree)
        merging_tree_size = len(merging_tree)

        validation_time = open(f'validation_time_{self.test_num}.csv', mode='a')
        validation_time_writer = csv.writer(validation_time, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        nodes_published = 0
        nodes_not_published = 0
        before_merge = time.time()

        # for kd_node in kdtree.level_order(merging_tree):
        #     if kd_node.data.parent_hash == '0':
        #         continue
        #     if not merged_into_tree.node_in_tree(kd_node):
        #         p_node = node_to_aggregate.blockchain.get_parent(kd_node)
        #         p_node_hash = BlockchainUtils.hash(p_node.data.to_json()).hexdigest()  # added hexdigest
        #         # print(f'p_node_hash: {p_node_hash}, kd_node.data.parent_hash: {kd_node.data.parent_hash}')
        #         if p_node_hash == kd_node.data.parent_hash:
        #             # need to publish
        #             self.publish(kd_node.data)
        #             # print(f'merge block published: {kd_node.data}')
        #             nodes_published += 1
        #     else:
        #         nodes_not_published += 1

        after_merge = time.time() - before_merge
        validation_time_writer.writerow([self.cluster_id, self.node_id,
                                         node_to_aggregate.node_id, merging_tree_size, nodes_published,
                                         nodes_not_published, after_merge])
        validation_time.close()
        node_to_aggregate.blockchain = copy.deepcopy(self.blockchain)
        node_to_aggregate.blockchain_size = copy.deepcopy(self.blockchain_size)
        node_to_aggregate.blockchain.blocks.size = copy.deepcopy(self.blockchain.blocks.size)
        node_to_aggregate.transaction_pool = copy.deepcopy(self.transaction_pool)

        # TODO:
        # for first_node, second_node in itertools.zip_longest(self.blockchain.blocks.level_order(),
        #                                                      agg_node.blockchain.blocks.level_order()):
        #     if first_node.blockchain.blocks.st_hash == second_node.blockchain.blocks.:
        #         continue
        #     '''#else:
        #     else:
        #
        #     '''
        # level order - for comparing trees
        # children iterator to verify parent hash
        # postorder if not verified to prune children

    def forge(self):
        forger = self.blockchain.next_forger()
        if forger == self.wallet.public_key_string():
            print('i am the forger')
            block = self.blockchain.create_block(
                self.transaction_pool.transactions, self.wallet)
            self.transaction_pool.remove_from_pool(
                self.transaction_pool.transactions)
            message = Message(self.p2p.socketConnector, 'BLOCK', block)
            self.p2p.broadcast(BlockchainUtils.encode(message))
        else:
            print('i am not the forger')

    def mkd_forge(self):
        node_coords = self.coords
        block_data = self.blockchain.create_block(node_coords, self.transaction_pool.transactions, self.wallet, self.node_id)
        self.transaction_pool.remove_from_pool(self.transaction_pool.transactions)
        block = block_data[0]
        block.parent_hash = BlockchainUtils.hash(block_data[1].to_json()).hexdigest()
        kdtree.create_subtree_hash(block_data[2])
        cluster_topic = self.cluster_id
        pub.unsubscribe(self.node_listener, cluster_topic)
        self.publish(block)
        self.blockchain_size += 1
        pub.subscribe(self.node_listener, cluster_topic)

    def request_chain(self):
        message = Message(self.p2p.socketConnector, 'BLOCKCHAINREQUEST', None)
        self.p2p.broadcast(BlockchainUtils.encode(message))

    def move_node(self, old_cluster_id, new_cluster_id):
        # node will change cluster id to new cluster
        old_topic = old_cluster_id #f'{self.test_num}.c{old_cluster_id}'  # + str(old_cluster_id).strip()
        new_topic = new_cluster_id  #f'{self.test_num}.c{new_cluster_id}'  # + str(new_cluster_id).strip()
        # old_cluster_size = len(self.blockchain.pos.stakers)

        if old_topic != new_topic:
            # publish self to old cluster: handler will see different cluster id and remove from POS
            # print(f'node {self.node_id} is about to publish itself')
            self.publish(self)
            self.cluster_id = new_cluster_id
            self.move_listener(old_topic, new_topic)
            # publish self to new cluster: handler will see same cluster id and add to POS
            self.publish(self)
            # TODO: move transaction publication to aggregator after validating the blocks

            # if old_cluster_size > 1:
            #     self.transaction_pool = TransactionPool()
            # else:  # publish transactions to new cluster
            #     for transaction in self.transaction_pool.transactions:
            #         self.publish(transaction)

    def to_json(self):
        bctj = self.blockchain.to_json() if self.blockchain is not None else ''
        j_data = {'node_id': self.node_id,
                  'cluster_id': self.cluster_id,
                  'blockchain': bctj,
                  'transaction_pool': self.transaction_pool.to_json(),
                  'wallet': self.wallet.to_json(),
                  'coords': self.coords}
        return j_data
