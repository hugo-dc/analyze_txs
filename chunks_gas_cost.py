import rpc

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

def save_gas_used(block_number, gas_used):
    gas_file = open(DATADIR+GASFILE, 'a')
    gas_file.write(str(block_number) + ',' + str(gas_used) + '\n')
    gas_file.close()

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

block_gas_usage = load_gas_used()

print(block_gas_usage)

# Read Code Merkleization log results containing total accessed chunks in a block
cm_result = read_csv(DATADIR+FILENAME)

data = []
out_file = open(DATADIR + OUTFILE, 'a')
rpc.set_rpc_endpoint('MAZLAB')
for line in cm_result:
    line_length = len(line)
    if line_length > 10:
        new_line = None
        block_number = parse_block_number(line[0])

        gas_used = 0
        if block_number in block_gas_usage.keys():
            print('found')
            gas_used = block_gas_usage[block_number]
        else:
            print('not found')
            rpc_result = rpc.get_block_by_number(block_number)
            if 'result' in rpc_result.keys(): 
                block = rpc_result['result']
                gas_used = int(block['gasUsed'], 16)
                block_gas_usage[block_number] = gas_used
                save_gas_used(block_number, gas_used)
            else:
                print("ERROR: Failed to get data for block", block_number)

        #print(block_number, gas_used)
        if line_length == 11:
            touched_chunks = int(line[10].strip())
            chunks_gas_cost = touched_chunks * CHUNK_COST
            total_gas = gas_used + chunks_gas_cost 
            inc_perc = "%.2f" % ((chunks_gas_cost / gas_used) * 100)
            #data.append(line + [str(gas_cost)])
            new_line = [str(block_number), str(gas_used), str(touched_chunks), str(chunks_gas_cost), str(total_gas), inc_perc]
        else:
            #data.append(line)
            touched_chunks = int(line[10].strip())
            chunks_gas_cost = int(line[11])
            total_gas = gas_used + chunks_gas_cost
            inc_perc = (chunks_gas_cost / gas_used) * 100
            new_line = [str(block_number), str(gas_used), str(touched_chunks), chunks_gas_cost, str(total_gas), "%.2f%" %  inc_perc]
        # block, gasUsed, chunks, chunksGasUsed, gasUsed+chunksGasUsed, % increase
        #data.append(new_line)
        print(new_line)
        out_file.write(','.join(new_line) + '\n')
out_file.close()

