import sys
import pprint
import json
import sha3
import requests


head = {"Content-type": "application/json"}
RPC_ENDPOINT = 'http://localhost:8545'


ts_file = open('prestate_tracer.js', 'r')
tracer_script = ts_file.read()
ts_file.close()


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
    print("\ntransaction", ix, ":", tx['hash'])
    print("from:", tx['from'])
    print("input:", tx['input'])
    if tx['to'] == None:
        print("\tdeploy contract")
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
                payload = {
                    'method': 'debug_traceTransaction',
                    'params': [tx['hash'], {'tracer': tracer_script}],
                    'id': 1
                }

                response = requests.post(RPC_ENDPOINT, data=json.dumps(payload), headers=head)

                result = response.json()['result']

                for r in result:
                    print('touched_account: ', r)

        except:
            print("ERROR with eth_getCode, response:", response.json())
            print(response.text)
