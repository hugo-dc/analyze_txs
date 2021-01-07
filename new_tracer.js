{
  ops: [],
  trace: null,
  callstack: [],
  cslen: [],
  cslencounter: 0,

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
        this_chunk_code_start = pos  // not used
      }
    }
    chunk = code.slice(this_chunk_start, code.length)

    chunks.push({'code_start': this_chunk_code_start, 'chunk': chunk.join('')})
    return chunks
  },
  
  step: function(log, db) {
    var addr = log.contract.getAddress()    
    if (this.trace === null) {
      this.trace = {}

      var acc = toHex(addr)
      if (this.trace[acc] === undefined) {
        var bytecode = toHex(db.getCode(addr))
        this.trace[acc] = {
          chunks: this.chunkify(bytecode), // each chunk is (<code_start>, <chunk> )
          touched_chunks: [], // TODO
          calls: []
        }
      }
    }
    var op = log.op.toString()



    if (op == 'CREATE' || op == 'CREATE2') {
      this.ops.push({ pc: log.getPC(), op: op, contract: toHex(addr) })
      var inOff = log.stack.peek(1).valueOf()
      var inEnd = inOff + log.stack.peek(2).valueOf()

      // Assemble the internal call report and store for completion
      var call = {
	type:    op,
	from:    toHex(addr),
        to:      '',
	input:   toHex(log.memory.slice(inOff, inEnd)),
	//gasIn:   log.getGas(),
	//gasCost: log.getCost(),
	value:   '0x' + log.stack.peek(0).toString(16)
      }
      
      this.callstack.push(call)
      this.cslencounter += 1
      this.cslen.push(this.cslencounter)
      return
    }

    if (op == 'SELFDESTRUCT') {
      this.ops.push({ pc: log.getPC(), op: op, contract: toHex(addr) })
      var left = this.callstack.length
      if (this.callstack[left-1].calls === undefined) {
	this.callstack[left-1].calls = []
      }
      this.callstack[left-1].calls.push({
	type:    op,
	from:    toHex(log.contract.getAddress()),
	to:      toHex(toAddress(log.stack.peek(0).toString(16))),
	//gasIn:   log.getGas(),
	//gasCost: log.getCost(),
	value:   '0x' + db.getBalance(log.contract.getAddress()).toString(16)
      })

      this.cslencounter += 1
      this.cslen.push(this.cslencounter)
      
      return      
    }

    if (op == 'CALL' || op == 'CALLCODE' || op == 'DELEGATECALL' || op == 'STATICCALL') {
      // Skip any pre-compile invocations, those are just fancy opcodes
      var to = toAddress(log.stack.peek(1).toString(16))
      this.ops.push({ pc: log.getPC(), op: op, contract: toHex(addr), calling: toHex(to) })
      if (isPrecompiled(to)) {
	return
      }

      // Add to the trace
      var acc = toHex(to)
      if (this.trace[acc] == undefined) {
        var bytecode = toHex(db.getCode(to))
        this.trace[acc] = {
          chunks: this.chunkify(bytecode),
          touched_chunks: [], // TODO
          calls: []
        }
        
      }
      
      var off = (op == 'DELEGATECALL' || op == 'STATICCALL' ? 0 : 1)

      var inOff = log.stack.peek(2 + off).valueOf()
      var inEnd = inOff + log.stack.peek(3 + off).valueOf()

      // Assemble the internal call report and store for completion
      var call = {
	type:    op,
	from:    toHex(log.contract.getAddress()),
	to:      toHex(to),
	input:   toHex(log.memory.slice(inOff, inEnd)),
	//gasIn:   log.getGas(),
	//gasCost: log.getCost(),
	outOff:  log.stack.peek(4 + off).valueOf(),
	outLen:  log.stack.peek(5 + off).valueOf()
      }
      
      if (op != 'DELEGATECALL' && op != 'STATICCALL') {
	call.value = '0x' + log.stack.peek(2).toString(16)
      }
      
      this.callstack.push(call)
      this.cslencounter += 1
      this.cslen.push(this.cslencounter)
      return
    }

    // If an existing call is returning, pop off the call stack
    if (op == 'REVERT') {
      this.ops.push({ pc: log.getPC(), op: op, contract: toHex(addr) })
      //this.callstack[this.callstack.length - 1].error = "execution reverted"
      return
    }
    //if (op == '
    //this.ops.push(log.getPC())
    //this.trace.push(log.op.toString())
    //this.ops.push(log.op.toString())
  },
  result: function(ctx, db) {
    // contracts
    // opcodes
    // callstack
    // cslen
    return { trace: this.trace,  opcodes: this.ops, callstack: this.callstack, cslen: this.cslen }
  },
  fault: function(log, db) {}
}
