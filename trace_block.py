import sys
import rpc
import json

def show_usage():
    print('usage:')
    print('\t', sys.argv[0] + ' <block_number>')
    exit(0)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        show_usage()
    block_number = int(sys.argv[1])
    block = rpc.get_block_by_number(block_number)
    print(json.dumps(block, indent=4))

