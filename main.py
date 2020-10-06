import sys
import pprint
import json
import sha3
import requests


head = {"Content-type": "application/json"}
RPC_ENDPOINT = 'http://localhost:8545'


# get block
def get_block(blocknum):
    payload = {
        'method': 'eth_getBlockByNumber',
        'params': [hex(blocknum), True],
        'id': 1
    }

    response = requests.post(RPC_ENDPOINT, data=json.dumps(payload), headers= head)

    #f = open('block_' + str(blocknum) + '.json', 'w')
    #f.write(str(response.json()['result']))
    #f.close()
    return response.json()['result']

number = int(sys.argv[1])

block = get_block(int(number))
#print(json.dumps(block, indent=4, sort_keys=True))

print("block number: ", block['number'])
print("total transactions: ", len(block['transactions']))

print(block['transactions'][0])

for ix, tx in enumerate(block['transactions']):
    print("transaction", ix, ":", tx['hash'])
    if tx['to'] == None:
        print("\tdeploy contract")
    else:
        print("\tgetting code for", tx['to'])
        payload = {
            'method': 'eth_getCode',
            'params': [tx['to'], hex(number)],
            'id': 1
        }
        response = requests.post(RPC_ENDPOINT, data=json.dumps(payload), headers=head)
        try:
            code = response.json()['result']
            print('\tcode:', code)
        except:
            print("ERROR with eth_getCode, response:", response.json())
            print(response.text)
    

