import requests
import json

head = {"Content-type": "application/json"}
RPC_LOCAL = 'http://localhost:8545'
RPC_INFURA = open('./infura_data.txt', 'r').read().strip()
RPC_MAZLAB = 'http://192.168.1.82:8545'

RPC_ENDPOINT = RPC_LOCAL # Change to infura/local if needed

CACHEDIR = './cache/'

ts_file = open('op_tracer.js', 'r')
tracer_script = ts_file.read()
ts_file.close()

def set_rpc_endpoint(ep):
    global RPC_ENDPOINT
    if ep == "INFURA":
        RPC_ENDPOINT = RPC_INFURA 
    elif ep == 'MAZLAB':
        RPC_ENDPOINT = RPC_MAZLAB
    else:
        RPC_ENDPOINT = RPC_LOCAL

def read_cache_file(fname):
    cache_file = open(fname, 'r')
    jsondata = cache_file.read().strip()
    if len(jsondata) == 0:
        jsondata = "{}"
    result = json.loads(jsondata)
    cache_file.close()
    return result

def write_cache_file(fname, data):
    cache_file = open(fname, 'w')
    cache_file.write(data)
    cache_file.close()

def get_block_by_number(blocknum):
    blocks = read_cache_file(CACHEDIR + 'blocks.json')

    if str(blocknum) in blocks.keys():
        return blocks[str(blocknum)]

    payload = {
        'method': 'eth_getBlockByNumber',
        'params': [hex(blocknum), True],
        'id': 1
    }

    response = requests.post(RPC_ENDPOINT, data=json.dumps(payload), headers= head)

    blocks[blocknum] = response.json()
    write_cache_file(CACHEDIR + 'blocks.json', json.dumps(blocks, indent=4, sort_keys=False))

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
        'params': [tx_hash, {'tracer': tracer}],
        'id': 1
    }
    response = requests.post(RPC_ENDPOINT, data=json.dumps(payload), headers = head)
    return response.json()
