import sys
import pprint
import json
import sha3
import requests


head = {"Content-type": "application/json"}
RPC_ENDPOINT = 'http://52.165.165.44:8545'


# get block
def get_block(blocknum):
    payload = {
        'method': 'eth_getBlockByNumber',
        'params': [hex(blocknum), True],
        'id': 1
    }

    response = requests.post(RPC_ENDPOINT, data=json.dumps(payload), headers= head)

    return response.json()['result']

block = get_block(1)

print(block)


