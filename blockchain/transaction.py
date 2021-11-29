import uuid
import time
import copy


class Transaction:

    def __init__(self, sender_public_key, receiver_public_key, amount, tr_type):
        self.sender_public_key = sender_public_key
        self.receiver_public_key = receiver_public_key
        self.amount = amount
        self.tr_type = tr_type
        self.id = (uuid.uuid1()).hex
        self.timestamp = time.time()
        self.signature = ''

    def to_json(self):
        return self.__dict__

    def sign(self, signature):
        self.signature = signature

    def payload(self):
        json_representation = copy.deepcopy(self.to_json())
        json_representation['signature'] = ''
        return json_representation

    def equals(self, transaction):
        if self.id == transaction.id:
            return True
        else:
            return False
