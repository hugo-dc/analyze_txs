import sys
import pprint
import json
import hashlib
import requests


head = {"Content-type": "application/json"}
RPC_ENDPOINT = 'http://localhost:8545'


ts_file = open('new_tracer.js', 'r')
tracer_script = ts_file.read()
ts_file.close()


def sha3_256(data):
    s = hashlib.sha3_256()
    s.update(data)
    return s.digest()

def chunkify(program):
    chunks = []
    pos = 0
    this_chunk_start = 0
    this_chunk_code_start = 0
    while pos < len(program):
        pos += (program[pos] - 0x5f) if (0x60 <= program[pos] <= 0x7f) else 1
        if pos >= this_chunk_start + 32:
            hash = sha3_256(
                    program[this_chunk_start:this_chunk_start + 32] +
                    this_chunk_code_start.to_bytes(32, 'big'))
            chunks.append(hash)
            this_chunk_start += 32
            this_chunk_code_start = pos
    return chunks

def get_current_block():
    payload = {
        'method': 'eth_blockNumber',
        'params': [],
        'id': 1
    }

    response = requests.post(RPC_ENDPOINT, data=json.dumps(payload), headers= head)

    return int(response.json()['result'], 16)


# get block
def get_block(blocknum):
    payload = {
        'method': 'eth_getBlockByNumber',
        'params': [hex(blocknum), True],
        'id': 1
    }

    response = requests.post(RPC_ENDPOINT, data=json.dumps(payload), headers= head)

    f = open('data/block_' + str(blocknum) + '.json', 'w')
    f.write(str(response.json()['result']))
    f.close()
    return response.json()

block_number = get_current_block()
response = get_block(block_number)
block = response['result']

print("block number: ", block_number)
print("total transactions: ", len(block['transactions']))


contract = ''
for ix, tx in enumerate(block['transactions']):
    if tx['to'] != None:
        payload = {
            'method': 'eth_getCode',
            'params': [tx['to'], hex(block_number)],
            'id': 1
        }
        response = requests.post(RPC_ENDPOINT, data=json.dumps(payload), headers=head)
        try:
            code = response.json()['result']
            if len(code) > 2:
                print("\ntransaction", ix, ":", tx['hash'])
                print("from:", tx['from'])
                print("to:  ", tx['to'])

                payload = {
                    'method': 'debug_traceTransaction',
                    'params': [tx['hash'], {'tracer': tracer_script}],
                    'id': 1
                }

                response = requests.post(RPC_ENDPOINT, data=json.dumps(payload), headers=head)
                result = response.json()['result']
                trace = result['trace']
                opcodes = result['opcodes']
                callstack = result['callstack']
                cslen = result['cslen']


                print('total opcodes: ', len(opcodes))
                print('depth: ', len(callstack))
                print('trace: ', trace.keys())

                print('opcodes:')
                print('pc\t\topcode\t\t\tcontract\t\t\tto')

                count = 0

                touched_opcodes = {}
                for op in opcodes:
                    contract = op['contract']
                    if op['op'] == 'CALL' or op['op'] == 'STATICCALL':
                        print(op['pc'], '\t\t', op['op'], '\t\t\t', op['contract'], callstack[count]['to'])
                        count += 1
                    else:
                        print(op['pc'], '\t\t', op['op'], '\t\t\t', op['contract'])

        except:
            print("ERROR with eth_getCode, response:", response.json())
            print(response.text)

