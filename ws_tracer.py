import time
import asyncio
import websockets
import json
import csv_util
import opcodes
import rpc
from rlp import decode

ts_file = open('op_tracer.js', 'r')
tracer_script = ts_file.read()
ts_file.close()

tx_trace_ids = {}

gas_guzzlers = {
	'0x7a250d5630b4cf539739df2c5dacb4c659f2488d': {
		'ofile': open('data/uniswap.csv', 'a'),
		'name': 'uniswap',
		},
	'0xdac17f958d2ee523a2206206994597c13d831ec7': {
		'ofile': open('data/usdt.csv', 'a'),
		'name': 'usdt',
		},
	'0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48': {
		'ofile': open('data/usdc.csv', 'a'),
		'name': 'usdc',
		},
	'0x881d40237659c251811cec9c364ef91dc08d300c': {
		'ofile': open('data/mm_swap.csv', 'a'),
		'name': 'mm_swap',
		},
	'0x11111112542d85b3ef69ae05771c2dccff4faa26': {
		'ofile': open('data/1inch.csv', 'a'),
		'name': '1inch',
		},
	'0x7d2768de32b0b80b7a3454c06bdac94a69ddc7a9': {
		'ofile': open('data/aave.csv', 'a'),
		'name': 'aave',
		},
}

tx_level_csv = []
block_level_csv = []

histogram_csv_file = open('data/histogram.csv', 'a')

invalid_csv_file = open('data/invalid.csv', 'a')

async def main():
	subscribed = False
	subId = ''
	async with websockets.connect('ws://127.0.0.1:9546') as websocket:
		while True:
			if not subscribed:
				payload = json.dumps({
					'method': 'eth_subscribe',
					'params': ['newHeads'],
					'id': 63,
					'jsonrpc': '2.0',
				})
				result = await websocket.send(payload)
				subscribed = True
		
			ev = await websocket.recv()
			msg = json.loads(ev)
			if 'id' in msg.keys() and msg['id'] == 63:
				print('subscribed', msg['result'])
				subId = msg['result']
			elif 'method' in msg.keys() and msg['method'] == 'eth_subscription' and msg['params']['subscription'] == subId:
				block_data = msg['params']['result']
				block_number = int(block_data['number'], 16)
				block = rpc.get_block_by_number(block_number)['result']
				for _, tx in enumerate(block['transactions']):
					if tx['to'] == None:
						continue
					tag = ''
					if tx['to'].lower() in gas_guzzlers.keys():
						tag = gas_guzzlers[tx['to'].lower()]['name']
					result = rpc.trace_transaction(tx['hash'], tracer_script)
					if 'result' in result.keys():
						tr_result = result['result']
						if tr_result['contract_call'] == True:
							tx_receipt = rpc.get_transaction_receipt(tx['hash'])['result']
							ctx_gas_used = tr_result['gas_used']
							gas_used = tx_receipt['gasUsed']	
							tx_opcount = opcodes.get_op_counter()
							histogram = tr_result['histogram']
							for op in histogram:
								tx_opcount = opcodes.update_op_counter(tx_opcount, op, histogram[op])
							# Write line into histogram file
							file_line = [str(block_number), tx['hash'], str(int(gas_used, 16))] + [str(tx_opcount[k]) if k in tx_opcount.keys() else '0' for k in opcodes.by_value.keys()]
							histogram_csv_file.write(','.join(file_line) + '\n')
							if tag != '':
								gas_guzzlers[tx['to']]['ofile'].write(','.join(file_line) + '\n')
							if tr_result['invalid']:
								gas = int(tx['gas'], 16)
								start_gas = tr_result['start_gas']
								end_gas = tr_result['end_gas']
								print(tx['to'])
								difference = int(gas_used, 16) - end_gas
								line = [str(block_number), tx['hash'], str(int(gas_used, 16)), str(end_gas), str(difference)]  #,  str(gas), str(start_gas), str(end_gas), str(ctx_gas_used), int(gas_used, 16)] #, str(gas_left)]
								print(': ', line)
								print('idc: ', tr_result['input_data_cost'])
								invalid_csv_file.write(','.join(line) + '\n')	
while 1:
	try:
	#if True:
		asyncio.get_event_loop().run_until_complete(main())
	except:
		print('reconnecting...')
		time.sleep(30)
