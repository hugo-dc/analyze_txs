import os
import json
import opcodes
import csv_util

TRACES_DIR = 'data/traces/'
BLOCKS_DIR = 'data/blocks/'
CSV_DATA = 'data/csv/'


def get_trace_fnames():
    trfiles = os.listdir(TRACES_DIR)
    trfiles.remove('.gitkeep')
    return trfiles

def read_file(fname):
    f = open(TRACES_DIR+fname, 'r')
    raw_data = f.read()
    f.close()
    json_data = json.loads(raw_data)
    return json_data

def sum_counters(opc1, opc2):
    for key in opc2:
        if key in opc1.keys():
            opc1[key] += opc2[key]
        else:
            opc1[key] = opc2[key]
    return opc1

def write_block_csv(block_log):
    fout = open(CSV_DATA + 'histogram_by_blocks.csv', 'w')
    for line in block_log:
        fout.write(','.join(line) + '\r\n')
    fout.close()


if __name__ == "__main__":
    trace_files = get_trace_fnames()
    tx_log = []

    block_log = []

    # Add block header
    block_header = get_csv_header(level='block')
    for h in block_header:
        block_log.append(h)

    for trace_fname in sorted(trace_files):
        try:
            trace_data = read_file(trace_fname)
        except:
            print('Error reading', trace_fname)
            continue
        print(trace_fname)
        block_number = list(trace_data.keys())[0]
        transactions = trace_data[block_number]

        #print(block_number)
        block_opcount = get_op_counter()

        block_line = []

        for tx in transactions:
            tx_opcount = get_op_counter()
            print(block_number, tx)
            histogram = transactions[tx]['histogram']
            for op in histogram:
                #print(op)
                try:
                    tx_opcount = update_counter(tx_opcount, op, histogram[op])
                except ValueError as err:
                    print(err)
                    print(tx, histogram, op)
                    exit(1)
            #print(tx_opcount)
            block_opcount = sum_counters(block_opcount, tx_opcount)

        block_line = [block_number, " "] + [str(block_opcount[k]) if k in block_opcount.keys() else '0' for k in opcodes.by_value.keys()]
        block_log.append(block_line)

write_block_csv(block_log)
