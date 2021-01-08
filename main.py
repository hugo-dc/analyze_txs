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

def get_current_block_number():
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

def write_log(number, lines):
    filename='data/log_' + str(number) + '.txt'
    output = open(filename, 'w')
    print('log length: ', len(lines))
    for line in lines:
        output.write(line + '\n')
    output.close()
    
def write_block(number, trace):
    filename='data/block_' + str(number) + '.json'
    output_file = open(filename, 'w')
    output_file.write(json.dumps(trace))
    output_file.close()
    print(filename)

block_trace = {} # Contains the result of a block execution
block_number = get_current_block_number()
block_trace[str(block_number)] = {} # The block trace will contains transactions calling contracts

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
        if len(code) > 2:  # check it's calling a contract
            transaction_trace = {'execution': [], 'contracts': []}
            #block_trace[str(block_number)].append({ tx['hash']: transaction_trace }) # stores current transaction hash
            block_trace[str(block_number)][ tx['hash'] ] = transaction_trace
            
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
            log_general = []
            execution_trace = []
            print('transaction: ', tx['hash'])
            print('opcodes: ', len(opcodes))
            for op in opcodes:
                contract = op['contract']
                pc = op['pc']

                # save opcode execution in trace
                #block_trace[str(block_number)][tx['hash']['execution'].append({ 'contract': contract, 'pc': pc, 'op': op['op'], 'calling': op['calling'] })
                if contract in touched_opcodes.keys():
                    touched_opcodes[contract].add(pc)
                else:
                    touched_opcodes[contract] = set([pc])
                if op['op'] == 'CALL' or op['op'] == 'STATICCALL':
                    line = str(op['pc']) + '\t\t' + op['op'] + '\t\t\t' + op['contract'] + ' ' + op['calling']
                    count += 1
                    execution_trace.append({'contract': contract, 'pc': pc, 'op': op['op'], 'calling': op['calling']})
                else:
                    line = str(op['pc']) + '\t\t' + op['op'] + '\t\t\t' + op['contract']
                    execution_trace.append({'contract': contract, 'pc': pc, 'op': op['op'], 'calling': ''})
                if contract not in log.keys():
                    log[contract] = [line]
                else:
                    log[contract].append(line)
                log_general.append(line)

            block_trace[str(block_number)][tx['hash']]['execution'] = execution_trace
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
write_log(block_number, log_general)

