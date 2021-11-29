from wallet import Wallet
from blockchain_utils import BlockchainUtils
import requests


def post_transaction(sender, receiver, amount, tr_type):
    transaction = sender.create_transaction(
        receiver.public_key_string(), amount, tr_type)
    url = "http://localhost:5000/transaction"
    package = {'transaction': BlockchainUtils.encode(transaction)}
    request = requests.post(url, json=package)


if __name__ == '__main__':

    bob = Wallet()
    alice = Wallet()
    alice.from_key('blockchain/keys/stakerPrivateKey.pem')  # added blockchain to file path
    exchange = Wallet()

    #forger: genesis
    post_transaction(exchange, alice, 100, 'EXCHANGE')
    post_transaction(exchange, bob, 100, 'EXCHANGE')
    post_transaction(exchange, bob, 10, 'EXCHANGE')

    # forger: probably alice
    post_transaction(alice, alice, 25, 'STAKE')
    post_transaction(alice, bob, 1, 'TRANSFER')
    post_transaction(alice, bob, 1, 'TRANSFER')
