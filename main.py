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
    #return response.json()['result']

number = int(sys.argv[1])

response = get_block(int(number))
#print("response: ", response)

block = response['result']
#print(json.dumps(block, indent=4, sort_keys=True))

#print(">", block)
print("block number: ", block['number'])
print("total transactions: ", len(block['transactions']))

#print(block['transactions'][0])

for ix, tx in enumerate(block['transactions']):
    #print("\ntransaction", ix, ":", tx['hash'])
    #print("from:", tx['from'])
    #print("input:", tx['input'])
    if tx['to'] == None:
        pass
        #print("\tdeploy contract")
    else:
        payload = {
            'method': 'eth_getCode',
            'params': [tx['to'], hex(number)],
            'id': 1
        }
        response = requests.post(RPC_ENDPOINT, data=json.dumps(payload), headers=head)
        try:
            code = response.json()['result']
            if len(code) > 2:
                print("\ntransaction", ix, ":", tx['hash'])
                print("from:", tx['from'])
                print("input:", tx['input'])
                print("code: ", code[2:])
                bytecode = bytes.fromhex(code[2:])
                chunks = chunkify(bytecode)
                print("chunks: ", len(chunks))
                payload = {
                    'method': 'debug_traceTransaction',
                    'params': [tx['hash'], {'tracer': tracer_script}],
                    'id': 1
                }

                response = requests.post(RPC_ENDPOINT, data=json.dumps(payload), headers=head)

                #print('response: ', response.json())
                pcs = response.json()['result']
                #print('PCs: ', result)
                used_chunks = []
                for pc in pcs:
                    c = int(pc) // 32
                    if c not in used_chunks:
                        used_chunks.append(c)
                        #print('PC: ', pc, ' - chunk: ', int(pc) // 32 + 1)
                print("touched chunks: ", len(used_chunks))
                print(":", used_chunks)
                

                #for r in result:
                    #print('touched_account: ', r)
                    ##print('code: ', response['result']['code'])

        except:
            print("ERROR with eth_getCode, response:", response.json())
            print(response.text)
