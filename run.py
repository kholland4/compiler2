#!/usr/bin/python3
import sys

reg = []
for i in range(256):
    #reg.append(bytes([0, 0, 0, 0]))
    reg.append([0, 0, 0, 0])

mem = bytearray([])
for i in range(65536):
    mem.append(0)

disk = []
with open("data.img", "rb") as f:
    dataByte = f.read(1)
    while dataByte and len(disk) < 256 * 1024:
        disk.append(int(ord(dataByte)))
        dataByte = f.read(1)

with open(sys.argv[1], "rb") as f:
    i = 0
    d = f.read(1)
    while d:
        mem[i] = ord(d)
        d = f.read(1)
        i += 1

pos = 0 #program counter (byte position)
offset = 0 #address space offset (bytes)
ilen = 4 #instruction length (bytes)

def regread(num):
    return (int(reg[num][0]) << 24) + (int(reg[num][1]) << 16) + (int(reg[num][2]) << 8) + int(reg[num][3])

def regwrite(num, data):
    reg[num][0] = int((data >> 24) & 255)
    reg[num][1] = int((data >> 16) & 255)
    reg[num][2] = int((data >> 8) & 255)
    reg[num][3] = int(data & 255)

busBuffer = 0

def busw(addr, data):
    global busBuffer
    if addr == 0: #stdio
        #sys.stdout.write(chr(data))
        sys.stdout.buffer.write(bytes([data & 255]))
        sys.stdout.flush()
    elif addr == 1: #control
        if data == 0:
            sys.exit()
    elif addr == 2: #disk
        if data >= 0 and data < len(disk):
            busBuffer = disk[data]

def busr():
    return busBuffer

while True:
    iindex = pos + offset
    opcode = mem[iindex]
    regA = mem[iindex + 1]
    regB = mem[iindex + 2]
    regQ = mem[iindex + 3]
    increment = True
    
    if opcode == 0: #noop
        pass
    elif opcode == 1: #chigh
        reg[regQ][0] = regA
        reg[regQ][1] = regB
    elif opcode == 2: #clow
        reg[regQ][2] = regA
        reg[regQ][3] = regB
    elif opcode == 3: #stor
        moffset = regread(regB)
        for i in range(4):
            val = reg[regA][i]
            mem[moffset + i] = val
    elif opcode == 4: #load
        moffset = regread(regB)
        for i in range(4):
            val = mem[moffset + i]
            reg[regQ][i] = val
        #print(("%4d: " % iindex) + "load addr %d (=%d) to reg %d" % (moffset, regread(regQ), regQ))
    elif opcode == 5: #jmp
        pos = regread(regB)
        increment = False
    elif opcode == 6: #branch
        #print(("%4d: " % iindex) + "conditional branch if %d (reg %d)" % (regread(regA), regA))
        if regread(regA) & 1 == 1:
            pos = regread(regB)
            increment = False
    elif opcode == 7: #local
        v = regread(regA)
        offset = regA
        pos = 0
        increment = False
    elif opcode == 8: #busr
        regwrite(regQ, busr())
    elif opcode == 9: #busw
        busw(regread(regA), regread(regB))
    elif opcode == 128: #add
        regwrite(regQ, regread(regA) + regread(regB)) #TODO: proper math; flags
    elif opcode == 129: #addc (add with carry)
        pass #TODO
    elif opcode == 130: #and
        regwrite(regQ, regread(regA) & regread(regB))
    elif opcode == 131: #or
        regwrite(regQ, regread(regA) | regread(regB))
    elif opcode == 132: #not
        regwrite(regQ, ~regread(regA))
    elif opcode == 133: #xor
        regwrite(regQ, regread(regA) ^ regread(regB)) #FIXME
    elif opcode == 134: #eq
        regwrite(regQ, int(regread(regA) == regread(regB)))
    elif opcode == 135: #gt
        regwrite(regQ, int(regread(regA) > regread(regB)))
    elif opcode == 136: #bsl
        regwrite(regQ, regread(regA) << 1)
    elif opcode == 137: #bsr
        regwrite(regQ, regread(regA) >> 1)
    elif opcode == 138: #copy
        regwrite(regQ, regread(regA))
    
    #print("%d: %3d %3d (%08x) %3d (%08x) %3d (%08x)" % (pos / ilen, opcode, regA, regread(regA), regB, regread(regB), regQ, regread(regQ)))
    
    if increment:
        pos += ilen
