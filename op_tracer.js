{
  histogram: {},
  gas_table: {},

  step: function(log, db) {
    //var op = log.op.toNumber().toString(16)
    var op = log.op.toString()

    if (this.histogram[op] === undefined) {
      this.histogram[op] = 1
    } else {
      this.histogram[op] += 1
    }

    if (this.gas_table[op] == undefined) {
      this.gas_table[op] = log.getCost()
    }
  },
  result: function(ctx, db) {
    return {
      'histogram': this.histogram,
      'gas_table': this.gas_table,
      'gas_used': ctx.gasUsed,
    }
  },
  fault: function(log, db){}
}
