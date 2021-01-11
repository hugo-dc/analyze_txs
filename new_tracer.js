{
  execution: [],
  contracts: {},

  chunkify: function(hexstring) {
    pos = 0
    code = []
    while (pos < hexstring.length) {
      hexbyte = hexstring.substring(pos, pos+2)
      code.push(hexbyte)
      pos += 2
    }
    
    chunks = []
    pos = 0
    this_chunk_start = 0
    this_chunk_code_start = 0
    while (pos < code.length) {
      byte = code[pos]

      if (0x60 <= byte && byte <= 0x7f) {
        pos += ( byte - 0x5f )
      } else {
        pos += 1
      }

      if (pos >= this_chunk_start + 32) {
        chunk = code.slice(this_chunk_start, this_chunk_start + 32)
        chunks.push({'code_start': this_chunk_code_start, 'chunk': chunk.join('')})
        this_chunk_start += 32
        this_chunk_code_start = pos
      }
    }
    chunk = code.slice(this_chunk_start, code.length)

    chunks.push({'code_start': this_chunk_code_start, 'chunk': chunk.join('')})
    return chunks
  },
  
  step: function(log, db) {
    var addr = log.contract.getAddress()    
    var acc = toHex(addr)
    var op = log.op.toString()
    var pc = log.getPC()
    var execution_trace = { contract: acc, pc: pc, op: op, calling: '' }

    if (this.contracts[acc] === undefined) {
      var bytecode = toHex(db.getCode(addr))
      var chunks = this.chunkify(bytecode)
      // save initial contract
      this.contracts[acc] = {
      code: bytecode,
      chunks: chunks,
      touched_chunks: [], // TODO
      calls: []           // TODO
      }
    }

    if (op == 'CREATE' || op == 'CREATE2') {
      execution_trace = { contract: acc, pc: pc, op: op, calling: 'NEW_CONTRACT' }
      return
    }

    if (op == 'SELFDESTRUCT') {
      return      
    }

    if (op == 'CALL' || op == 'CALLCODE' || op == 'DELEGATECALL' || op == 'STATICCALL') {
      // Skip any pre-compile invocations, those are just fancy opcodes
      var to = toAddress(log.stack.peek(1).toString(16))
      execution_trace = { contract: acc, pc: pc, op: op, calling: toHex(to) }
      if (isPrecompiled(to)) {
	return
      }

      // TODO: add contract to this.contracts
      return
    }

    // If an existing call is returning, pop off the call stack
    if (op == 'REVERT') {
      return
    }
    this.execution.push(execution_trace)
  },
  result: function(ctx, db) {
	  // {
	  // 	execution: [ { contract, pc, op, calling } ]
	  // 	contracts: { address: { code, chunks, touched_chunks } }
	  // }
	  return {
		  execution : this.execution,
		  contracts : this.contracts,
	  }
  },
  fault: function(log, db) {}
}
