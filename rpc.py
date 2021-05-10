import requests
import json

head = {"Content-type": "application/json"}
RPC_LOCAL = 'http://localhost:8545'
RPC_INFURA = open('./infura_data.txt', 'r').read().strip()

RPC_ENDPOINT = RPC_LOCAL # Change to infura if needed

ts_file = open('op_tracer.js', 'r')
tracer_script = ts_file.read()
ts_file.close()

def get_block_by_number(blocknum):
    payload = {
        'method': 'eth_getBlockByNumber',
        'params': [hex(blocknum), True],
        'id': 1
    }

    response = requests.post(RPC_ENDPOINT, data=json.dumps(payload), headers= head)
    return response.json()

def get_transaction_receipt(tx_hash):
    payload = {
        'method': 'eth_getTransactionReceipt',
        'params': [tx_hash],
        'id': 1
    }
    response = requests.post(RPC_ENDPOINT, data=json.dumps(payload), headers = head)
    return response.json()

def trace_transaction(tx_hash, tracer):
    payload = {
        'method': 'debug_traceTransaction',
        'params': [tx_hash, {'tracer': tracer, 'timeout': '500s'}],
        'id': 1
    }
    response = requests.post(RPC_ENDPOINT, data=json.dumps(payload), headers = head)
    return response.json()

