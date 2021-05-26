{
  contracts: {},
  extcodecopy_found: false,
  
  touchPC: function(contract, pc) {
    var touchedChunk = Math.floor(pc / 32)

    if (this.contracts[contract]['chunks'].indexOf(touchedChunk) < 0) {
      this.contracts[contract]['chunks'].push(touchedChunk)
    }
  },
  touchRange: function(contract, from, to) {
    var fcid = Math.floor(from / 32)
    var tcid = Math.floor(to / 32)

    for (i = fcid; i < tcid + 1; i++) {
      if (this.contracts[contract]['chunks'].indexOf(touchedChunk) < 0) {
        this.contracts[contract]['chunks'].push(i)
      }
    }
  },
  step: function(log, db) {
    var addr = toHex(log.contract.getAddress())
    var op = log.op.toString()
    var pc = log.getPC()

    if (!(addr in this.contracts)) {
      this.contracts[addr] = { 'chunks': [] }
    }

    this.touchPC(addr, pc)

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
      'contracts': this.contracts,
    }
  },
  fault: function(log, db) {
  }
}
