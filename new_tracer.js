{
  ops: [],
  
  step: function(log, db) {
    this.ops.push(log.getPC())
    //this.ops.push(log.op.toString())
  },
  result: function(ctx, db) {
    return this.ops
  },
  fault: function(log, db) {}
}
