import uuid
import time
import copy


class SensorTransaction:
    # check UUID, 3 should be used instead of 1 so the network address
    # isn't used to make the ID
    def __init__(self, sender_public_key, reading, tr_type='SENSOR'):
        self.sender_public_key = sender_public_key
        self.reading = reading
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
