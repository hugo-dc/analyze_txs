import rpc
import time
import sys

DATADIR = './data/'
FILENAME = 'cm-result.csv'
OUTFILE = 'chunks_cost.csv'
GASFILE = 'gas_used.csv'

CHUNK_COST = 350

def read_csv(file):
    fin = open(file, 'r')
    data = fin.read()
    fin.close()
    data = data.split('\n')
    data = [line.split(',') for line  in data]
    return data

def parse_block_number(block):
    if block.find('EXTRA') > 0:
        garbage, block = block.split(')')
    return int(block.strip())

def load_gas_used():
    gas_file = open(DATADIR + GASFILE, 'r')
    gas_data = gas_file.read()
    gas_data = gas_data.split('\n')
    result = {}
    for line in gas_data:
        fields = line.split(',')
        if len(fields) != 2:
            continue
        block = int(fields[0])
        gas_used = int(fields[1])
        result[block] = gas_used
    gas_file.close()
    return result

initial_block = None
if len(sys.argv) == 2:
    initial_block = int(sys.argv[1])

# Read Code Merkleization log results containing total accessed chunks in a block
print('Reading cm-result.csv ...')
cm_result = read_csv(DATADIR+FILENAME)

print('Processing...')
data = []
out_file = open(DATADIR + OUTFILE, 'a')
rpc.set_rpc_endpoint('LOCAL')
for line in cm_result:
    line_length = len(line)
    if line_length > 10:
        new_line = None
        block_number = parse_block_number(line[0])

        if initial_block != None and block_number < initial_block:
            print("Ignoring block", block_number)
            continue

        gas_used = 0
        try:
            rpc_result = rpc.get_block_by_number(block_number)
        except:
            print("Error found in: ", line)
            time.sleep(20)
            rpc_result = rpc.get_block_by_number(block_number)

        if 'result' in rpc_result.keys(): 
            block = rpc_result['result']
            gas_used = int(block['gasUsed'], 16)
        else:
            print("ERROR: Failed to get data for block", block_number)

        if line_length == 11:
            touched_chunks = int(line[10].strip())
            chunks_gas_cost = touched_chunks * CHUNK_COST
            total_gas = gas_used + chunks_gas_cost 
            inc_perc = "%.2f" % ((chunks_gas_cost / gas_used) * 100)
            new_line = [str(block_number), str(gas_used), str(touched_chunks), str(chunks_gas_cost), str(total_gas), inc_perc]
        else:
            touched_chunks = int(line[10].strip())
            chunks_gas_cost = int(line[11])
            total_gas = gas_used + chunks_gas_cost
            inc_perc = (chunks_gas_cost / gas_used) * 100
            new_line = [str(block_number), str(gas_used), str(touched_chunks), str(chunks_gas_cost), str(total_gas), "%.2f" %  inc_perc]
        # block, gasUsed, chunks, chunksGasUsed, gasUsed+chunksGasUsed, % increase
        print(new_line)
        out_file.write(','.join(new_line) + '\n')
out_file.close()

