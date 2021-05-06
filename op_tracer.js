{
  histogram: {},
  gas_left: [],
  gas_table: {},
  contract_call: false,
  invalid: false,
  input_data: null,
  input_data_cost: 0,
  ops: [],

  step: function(log, db) {
    this.contract_call = true
    var op = log.op.toString()

    if (this.histogram[op] === undefined) {
      this.histogram[op] = 1
    } else {
      this.histogram[op] += 1
    }

    this.gas_left.push(log.getGas())

    if (this.gas_table[op] == undefined) {
      this.gas_table[op] = log.getCost()
    }

    this.ops.push(log.getCost())
    if (log.op.toNumber() == 0xfe) {
        this.invalid = true
    }

    input_data = log.contract.getInput()
    if (this.input_data == null && input_data) {
	this.input_data = input_data	
	for(var i = 0; i < this.input_data.length; i++) {
		if (this.input_data[i] == 0) {
			this.input_data_cost = this.input_data_cost + 4	
		} else {
			this.input_data_cost = this.input_data_cost + 68
		}
	}
    }
  },
  result: function(ctx, db) {
    var gas_used = this.gas_left[0] - this.gas_left[this.gas_left.lenght - 1] 
    return {
      'histogram': this.histogram,
      'gas_table': this.gas_table,
      'start_gas': this.gas_left[0],
      'end_gas': this.gas_left[this.gas_left.length - 1],
      'gas_used': ctx.gasUsed,
      'invalid': this.invalid,
      'input_data': this.input_data,
      'input_data_cost': this.input_data_cost,
      'contract_call': this.contract_call,
      'ops': this.ops,
    }
  },
  fault: function(log, db){}
}

