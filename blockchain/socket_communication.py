from p2pnetwork.node import Node
from peer_discovery_handler import PeerDiscoveryHandler
from socket_connector import SocketConnector
from blockchain_utils import BlockchainUtils
import json


class SocketCommunication(Node):

    def __init__(self, ip, port):
        super(SocketCommunication, self).__init__(ip, port, None)
        self.peers = []
        self.peerDiscoveryHandler = PeerDiscoveryHandler(self)
        self.socketConnector = SocketConnector(ip, port)

    def connectToFirstNode(self):
        if self.socketConnector.port != 10001:
            self.connect_with_node('localhost', 10001)

    def startSocketCommunication(self, node):
        self.node = node
        self.start()
        self.peerDiscoveryHandler.start()
        self.connectToFirstNode()

    def inbound_node_connected(self, connected_node):
        self.peerDiscoveryHandler.handshake(connected_node)

    def outbound_node_connected(self, connected_node):
        self.peerDiscoveryHandler.handshake(connected_node)

    def node_message(self, connected_node, message):
        message = BlockchainUtils.decode(json.dumps(message))
        if message.message_type == 'DISCOVERY':
            self.peerDiscoveryHandler.handleMessage(message)
        elif message.message_type == 'TRANSACTION':
            transaction = message.data
            self.node.handle_transaction(transaction)
        elif message.message_type == 'BLOCK':
            block = message.data
            self.node.handle_block(block)
        elif message.message_type == 'BLOCKCHAINREQUEST':
            self.node.handle_blockchain_request(connected_node)
        elif message.message_type == 'BLOCKCHAIN':
            blockchain = message.data
            self.node.handle_blockchain(blockchain)

    def send(self, receiver, message):
        self.send_to_node(receiver, message)

    def broadcast(self, message):
        self.send_to_nodes(message)
