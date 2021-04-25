import opcodes

def get_csv_header(level):
	initial_fields = ''
	if level == 'block':
		initial_fields = ["Block #", "Gas Used"] 
	if level == 'transaction':
		initial_fields = ["Block #", "Transactions", "Gas Used"]
	return [
		initial_fields
		+ list(opcodes.by_name.keys()),  # Line 1: initial fields and opcode numbers
		([" "] * len(initial_fields))
		+ [ str(k) for k in opcodes.by_value.keys()]  # Line 2: blanks below initial fields and opcode numbers
	]

