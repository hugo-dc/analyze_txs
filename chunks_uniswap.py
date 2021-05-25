import time
import rpc

gas_guzzlers = {
	'0x7a250d5630b4cf539739df2c5dacb4c659f2488d': {
		'ofile': open('data/chunks_uniswap.csv', 'a'),
		'name': 'uniswap',
		},
	#'0xdac17f958d2ee523a2206206994597c13d831ec7': {
		#'ofile': open('data/chunks_usdt.csv', 'a'),
		#'name': 'usdt',
		#},
	#'0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48': {
		#'ofile': open('data/chunks_usdc.csv', 'a'),
		#'name': 'usdc',
		#},
	'0x881d40237659c251811cec9c364ef91dc08d300c': {
		'ofile': open('data/chunks_mm_swap.csv', 'a'),
		'name': 'mm_swap',
		},
	'0x11111112542d85b3ef69ae05771c2dccff4faa26': {
		'ofile': open('data/chunks_1inch.csv', 'a'),
		'name': '1inch',
		},
	'0x7d2768de32b0b80b7a3454c06bdac94a69ddc7a9': {
		'ofile': open('data/chunks_aave.csv', 'a'),
		'name': 'aave',
		},
}

ts_file = open('chunks_cost.js', 'r')
tracer = ts_file.read()
ts_file.close()

# Get the latest block number
result = rpc.block_number()
block_number = 0
if 'result' in result.keys():
    block_number = int(result['result'], 16)

block_number = block_number - 100
while True:
    block = rpc.get_block_by_number(block_number)['result']
    if block == None:
        time.sleep(30)
        continue

    print('==================================')
    print(block_number)

    for tx in block['transactions']:
        if 'to' in tx.keys() and tx['to'] != None:
            if tx['to'].lower() in gas_guzzlers.keys():
                contract_name = gas_guzzlers[tx['to']]['name']
                print(contract_name)
                result = rpc.trace_transaction(tx['hash'], tracer) 
                print(result)
                input()
    block_number += 1


