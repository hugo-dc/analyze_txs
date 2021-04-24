import asyncio
import websockets
import json
from rlp import decode

ts_file = open('op_tracer.js', 'r')
tracer_script = ts_file.read()
ts_file.close()

tx_trace_ids = {}

UNISWAP = '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D'

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
				for _, tx in enumerate(block['transactions']):
					tag = ''
					if tx['to'] == UNISWAP:
						tag = 'uniswap'
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
						'tag': tag,
						'traced': False,
					}			
					count += 1
					await websocket.send(payload)
			elif 'id' in msg.keys() and msg['id'] >= 65:
				tx_id = msg['id']
				print(msg)
				#print(tx_trace_ids[tx_id])
				if 'result' in msg.keys():
					print(msg['result'])
					tx_trace_ids[tx_id]['traced'] = True
				else:
					if 'error' in msg.keys():
						# TODO: Try tracing again
						tx_hash = tx_trace_ids[tx_id]['transaction']
						print(tx_hash, msg['error']['message'])
						payload = json.dumps({
							'method': 'debug_traceTransaction',
							'params': [tx_hash, {'tracer': tracer_script}],
							'id': tx_id,
							'jsonrpc': '2.0',
						})

						await websocket.send(payload)

asyncio.get_event_loop().run_until_complete(main())
