import sys
import json
import hashlib
import requests

head = {"Content-type": "application/json"}
RPC_ENDPOINT = 'http://localhost:8545'

ts_file = open('op_tracer.js', 'r')
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

def write_file(fname, data):
    output_file = open(fname, 'w')
    output_file.write(data)
    output_file.close()

def write_trace(number, trace):
    write_file('data/traces/trace_block_' + str(number) + '.json', json.dumps(trace, indent=4))

def write_block(number, block_json):
    filename='data/blocks/block_' + str(number) + '.json' 
    write_file(filename, json.dumps(block_json, indent=4))

def write_gas_table(gas_table):
    filename='data/gas_table.json'
    write_file(filename, json.dumps(gas_table, indent=4))

last_block = get_current_block_number()
start_block = last_block - 50 

contracts = {}

block_number = start_block

gas_table = {}

while True:
    block_trace = {}
    block_trace[str(block_number)] = {}

    response = get_block(block_number)

    #try:
    #if True:
    block = response['result']
    write_block(block_number, block)
    #except:
    #    print("Failed to retrieve block", block_number)
    #    sleep(30)

    if not 'transactions' in block.keys():
        print("???: ", block_number)
        exit(1)

    print("Tracing block:", block_number, "[", len(block['transactions']), "]")

    contract = ''
    ccall_found = False
    for ix, tx in enumerate(block['transactions']):
        if tx['to'] != None:
            if tx['to'] in contracts.keys():
                code = contracts[tx['to']]
            else:
                payload = {
                    'method': 'eth_getCode',
                    'params': [tx['to'], hex(block_number)],
                    'id': 1
                }
                response = requests.post(RPC_ENDPOINT, data=json.dumps(payload), headers=head)
                try:
                    code = response.json()['result']
                    if len(code) > 2:
                        contracts[tx['to']] = code
                except:
                    print("Error while trying to get code for account", tx['to'])
                    break

            if len(code) > 2:
                ccall_found = True # TODO: Store found contract address in a list, so we don't need to call getCode
                payload = {
                    'method': 'debug_traceTransaction',
                    'params': [tx['hash'], {'tracer': tracer_script}],
                    'id': 1
                }
    
                #print('Tx: ', tx['hash'])
                
                try:
                    response = requests.post(RPC_ENDPOINT, data=json.dumps(payload), headers=head)
                    result = response.json()['result']
                    #execution = result['execution']
                    #contracts = result['contracts']
                    block_trace[str(block_number)][tx['hash']] = { 'histogram': {}, 'gas_used': 0 }
                    block_trace[str(block_number)][tx['hash']]['histogram'] = result['histogram']
                    block_trace[str(block_number)][tx['hash']]['gas_used'] = result['gas_used']

                    table = result['gas_table']

                    for k in table.keys():
                        if k not in gas_table.keys():
                            gas_table[k] = table[k]

                except:
                    print("Error")
                    print(response.json())
                    print(len(contracts))
                    block_number = get_current_block_number() - 50 
                    break

    if ccall_found:
        write_trace(block_number, block_trace)
        write_gas_table(gas_table)


    block_number = block_number + 1
