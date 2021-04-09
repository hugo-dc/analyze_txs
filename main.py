import sys
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

def write_block(number, trace):
    filename='data/block_' + str(number) + '.json'
    output_file = open(filename, 'w')
    output_file.write(json.dumps(trace, indent=4))
    output_file.close()
    print(filename)

# block_number {
#                tx1: { execution: [ { contract, pc, op, calling } ],
#                       contracts: { address : { code, chunks, touched_chunks } }
# }

#end_block = get_current_block_number()
#start_block = 0  #end_block - 50 


block_number = 0
while True:
    block_trace = {}
    block_trace[str(block_number)] = {}

    response = get_block(block_number)

    try:
        block = response['result']
    except:
        print("Failed to retrieve block", block_number)
        sleep(30)

    if not 'transactions' in block.keys():
        print("???: ", block)
        continue

    print("Tracing block:", block_number, "[", len(block['transactions']), "]")

    contract = ''
    ccall_found = False
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
            except:
                #print("Error while trying to get code for account", tx['to'])
                continue

            if len(code) > 2:
                ccall_found = True # TODO: Store found contract address in a list, so we don't need to call getCode
                payload = {
                    'method': 'debug_traceTransaction',
                    'params': [tx['hash'], {'tracer': tracer_script}],
                    'id': 1
                }
    
                print('Tx: ', tx['hash'])
                response = requests.post(RPC_ENDPOINT, data=json.dumps(payload), headers=head)
                try:
                    result = response.json()['result']
                    execution = result['execution']
                    contracts = result['contracts']
                    block_trace[str(block_number)][tx['hash']] = { 'execution': [], 'contracts': {} }
                    block_trace[str(block_number)][tx['hash']]['execution'] = execution
                    block_trace[str(block_number)][tx['hash']]['contracts'] = contracts
                except:
                    print("Error")

    if ccall_found:
        write_block(block_number, block_trace)

    block_number = block_number + 1
