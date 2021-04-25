{
  histogram: {},
  gas_left: 0,
  gas_table: {},
  contract_call: false,

  step: function(log, db) {
    this.contract_call = true
    var op = log.op.toString()

    if (this.histogram[op] === undefined) {
      this.histogram[op] = 1
    } else {
      this.histogram[op] += 1
    }

    this.gas_left = log.getGas()

    if (this.gas_table[op] == undefined) {
      this.gas_table[op] = log.getCost()
    }
  },
  result: function(ctx, db) {
    return {
      'histogram': this.histogram,
      'gas_table': this.gas_table,
      'gas_used': ctx.gasUsed,
      'gas_left': this.gas_left,
      'contract_call': this.contract_call,
    }
  },
  fault: function(log, db){}
}
