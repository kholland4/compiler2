#!/usr/bin/python3
import sys

ops = {
  "noop": 0,
  "chigh": 1,
  "clow": 2,
  "stor": 3,
  "load": 4,
  "jmp": 5,
  "branch": 6,
  "local": 7,
  "busr": 8,
  "busw": 9,
  "add": 128,
  "addc": 129,
  "and": 130,
  "or": 131,
  "not": 132,
  "xor": 133,
  "eq": 134,
  "gt": 135,
  "bsl": 136,
  "bsr": 137,
  "copy": 138
}

code = ""
with open(sys.argv[1], "r") as f:
    code = f.read()

prog = bytearray([])

for line in code.split("\n"):
    sects = line.split(" ")
    if len(sects) >= 1:
        if sects[0] in ops:
            opcode = ops[sects[0]]
            regA = 0
            regB = 0
            regQ = 0
            if len(sects) >= 2:
                regA = int(sects[1])
            if len(sects) >= 3:
                regB = int(sects[2])
            if len(sects) >= 4:
                regQ = int(sects[3])
            
            prog.append(opcode)
            prog.append(regA)
            prog.append(regB)
            prog.append(regQ)

with open("program.bin", "wb") as f:
    f.write(prog)
