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

def get_current_block():
    payload = {
        'method': 'eth_blockNumber',
        'params': [],
        'id': 1
    }
    response = requests.post(RPC_ENDPOINT, data=json.dumps(payload), headers= head)
    return int(response.json()['result'], 16)


def get_block(blocknum):
    payload = {
        'method': 'eth_getBlockByNumber',
        'params': [hex(blocknum), True],
        'id': 1
    }

    response = requests.post(RPC_ENDPOINT, data=json.dumps(payload), headers= head)
    return response.json()

def write_block(number, trace):
    output_file = open('data/block_' + str(number) + '.json', 'w')
    output_file.write(json.dumps(trace))
    output_file.close()

block_trace = {} # Contains the result of a block execution
block_number = get_current_block()
block_trace[str(block_number)] = [] # The block trace will contain a list of transactions calling contracts

response = get_block(block_number)
block = response['result']

contract = ''
for ix, tx in enumerate(block['transactions']):
    if tx['to'] != None:
        payload = {
            'method': 'eth_getCode',
            'params': [tx['to'], hex(block_number)],
            'id': 1
        }
        response = requests.post(RPC_ENDPOINT, data=json.dumps(payload), headers=head)
        code = response.json()['result']
        if len(code) > 2:
            transaction_trace = {'execution': [], 'contracts': []}
            block_trace[str(block_number)].append({ tx['hash']: transaction_trace })
            
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

            count = 0
            touched_opcodes = {}
            log = {}
            for op in opcodes:
                contract = op['contract']
                pc = op['pc']
                if contract in touched_opcodes.keys():
                    touched_opcodes[contract].add(pc)
                else:
                    touched_opcodes[contract] = set([pc])
                if op['op'] == 'CALL' or op['op'] == 'STATICCALL':
                    line = str(op['pc']) + '\t\t' + op['op'] + '\t\t\t' + op['contract'] + ' ' + op['calling']
                    count += 1
                else:
                    line = str(op['pc']) + '\t\t' + op['op'] + '\t\t\t' + op['contract']
                if contract not in log.keys():
                    log[contract] = [line]
                else:
                    log[contract].append(line)
                    
            for k in touched_opcodes.keys():
                pcs = list(touched_opcodes[k])
                chunks = set()
                for pc in pcs:
                    chunk = pc // 32
                    chunks.add(chunk)
                chunks = list(chunks)
                chunks.sort()
                lines = log[k]

write_block(block_number, block_trace)

