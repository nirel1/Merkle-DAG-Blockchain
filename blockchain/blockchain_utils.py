from Crypto.Hash import SHA1
import json
import jsonpickle


class BlockchainUtils:

    @staticmethod
    def hash(data):
        data_string = json.dumps(data)
        data_bytes = data_string.encode('utf-8')
        data_hash = SHA1.new(data_bytes)
        return data_hash

    @staticmethod
    def encode(object_to_encode):
        return jsonpickle.encode(object_to_encode, unpicklable=True)

    @staticmethod
    def decode(encoded_object):
        return jsonpickle.decode(encoded_object)
