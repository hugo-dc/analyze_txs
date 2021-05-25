{
  contracts: {},
  chunks: {},
  execution: [],
  touchPC: function(contract, pc) {
    if (!(contract in this.contracts)) {
      this.contracts[contract] = {}  
    }

    var touchedChunk = Math.floor(pc / 32)
    this.chunks[touchedChunk] = true
    this.contracts[contract][touchedChunk] = true
  },
  touchRange: function(contract, from, to) {
    var fcid = Math.floor(from / 32)
    var tcid = Math.floor(to / 32)

    for (i = fcid; i < tcid + 1; i++) {

    }
  },
  step: function(log, db) {
    var addr = toHex(log.contract.getAddress())
    var op = log.op.toString()
    var pc = log.getPC()
   
    this.touchPC(addr, pc)
    this.execution.push([pc, op])
    // CODECOPY
    if (op == 'CODECOPY') {
      // get offset
      var codeOffset = log.stack[0]
      // get length
      var length = log.stack[1]
      this.touchRange(addr, codeOffset, codeOffset+length)
    }
    // EXTCODECOPY
    if (op == 'EXTCODECOPY') {
      // get address
      var address = log.stack[0]
      // get offset
      var offset = log.stack[1]
      // get length
      var length = log.stack[2]
      this.touchRange(addr, offset, offset+length)
    }
  },
  result: function(ctx, db) {
    return {
      //'execution': this.execution,
      'contracts': this.contracts,
      //'chunks': this.chunks,
    }
  },
  fault: function(log, db) {
  }
}
