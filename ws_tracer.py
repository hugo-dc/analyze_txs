import asyncio
import websockets
import json
import csv_util
import opcodes
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

#UNISWAP = '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D'

tx_level_csv = []
block_level_csv = []

histogram_csv_file = open('data/histogram.csv', 'a')
#uniswap_csv_file = open('data/uniswap.csv', 'a')

#file_header = csv_util.get_csv_header(level='transaction')
# Write header into file
#for h in file_header:
#	histogram_csv_file.write(','.join(h) + '\n')


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
				print(result)
				subscribed = True
		
			ev = await websocket.recv()
			msg = json.loads(ev)
			#print('>', msg)
			if 'id' in msg.keys() and msg['id'] == 63:
				print('subscribed', msg['result'])
				subId = msg['result']
			elif 'method' in msg.keys() and msg['method'] == 'eth_subscription' and msg['params']['subscription'] == subId:
				block_data = msg['params']['result']
				#print(json.dumps(block_data, indent=4))
				#print(block_data['number'])
				payload = json.dumps({
					'method': "eth_getBlockByNumber",
					'params': [block_data['number'], True],
					'id': 64,
					'jsonrpc': '2.0',
				})
				await websocket.send(payload)
			elif 'id' in msg.keys() and msg['id'] == 64:
				block = msg['result']
				count = 0
				print('>>>', int(block['number'], 16))
				for _, tx in enumerate(block['transactions']):
					if tx['to'] == None:
						continue
					tag = ''
					if tx['to'].lower() in gas_guzzlers.keys():
						tag = gas_guzzlers[tx['to'].lower()]['name']
					tx_id = 65 + count
					payload = json.dumps({
						'method': 'debug_traceTransaction',
						'params': [tx['hash'], {'tracer': tracer_script}],
						'id': tx_id,
						'jsonrpc': '2.0',
					})
					#print(tx_id, '-', tx['hash'])
					tx_trace_ids[tx_id] = (tx['blockNumber'], tx['hash'])
					tx_trace_ids[tx_id] = { 
						'blockNumber': tx['blockNumber'],
						'transaction': tx['hash'],
						'to': tx['to'].lower(),
						'gas': tx['gas'],
						'tag': tag,
						'traced': False,
					}			
					count += 1
					await websocket.send(payload)
			elif 'id' in msg.keys() and msg['id'] >= 65:
				tx_id = msg['id']
				#print(tx_trace_ids[tx_id])
				if 'result' in msg.keys():
					#print(msg['result'])
					tx_trace_ids[tx_id]['traced'] = True
					tr_result = msg['result']

					# Only save trace results for txs calling contracts
					if tr_result['contract_call'] == True: 
						block_number = str(tx_trace_ids[tx_id]['blockNumber'])
						tx_hash = tx_trace_ids[tx_id]['transaction']
						tx_to = tx_trace_ids[tx_id]['to']
						tag = tx_trace_ids[tx_id]['tag']
						histogram = msg['result']['histogram']
						gas = int(tx_trace_ids[tx_id]['gas'], 16)
						gas_used = str(msg['result']['gas_used'])
						gas_left = msg['result']['gas_left']

						#print(tx_hash, gas_used)
						tx_opcount = opcodes.get_op_counter()
						for op in histogram:
							tx_opcount = opcodes.update_op_counter(tx_opcount, op, histogram[op])
						# Write line into histogram file
						# Gets the correct order of opcodes, and write the value found in the trace, if the opcode is not found, then writes 0
						file_line = [block_number, tx_hash, gas_used] + [str(tx_opcount[k]) if k in tx_opcount.keys() else '0' for k in opcodes.by_value.keys()]
						histogram_csv_file.write(','.join(file_line) + '\n')
						if tag != '':
							gas_guzzlers[tx_to]['ofile'].write(','.join(file_line) + '\n')
				else:
					if 'error' in msg.keys():
						# TODO: Try tracing again
						tx_hash = tx_trace_ids[tx_id]['transaction']
						print('>>', tx_hash, msg['error']['message'])
						payload = json.dumps({
							'method': 'debug_traceTransaction',
							'params': [tx_hash, {'tracer': tracer_script}],
							'id': tx_id,
							'jsonrpc': '2.0',
						})

						await websocket.send(payload)

while 1:
	try:
		asyncio.get_event_loop().run_until_complete(main())
	except:
		print('...')
