#!/usr/bin/python3
import sys, string, math

FLAG_WORD_SIZE = 4
FLAG_ILEN = 4

code = ""
with open(sys.argv[1], "r") as f:
    code = f.read()

class Symbol:
    type = None
    value = None
    subtype = None
    
    def __init__(self, _type, _value = None, _subtype = None):
        self.type = _type
        self.value = _value
        self.subtype = _subtype
    
    def __repr__(self):
        if self.value == None:
            if self.subtype == None:
                return self.type
            else:
                return "%s.%s" % (self.type, self.subtype)
        else:
            if self.subtype == None:
                return "%s: %s" % (self.type, self.value)
            else:
                return "%s.%s: %s" % (self.type, self.subtype, self.value)

def sread(idx):
    #"Safely" read a char from a string - returns a null char when out of bounds
    if idx < len(code):
        return code[idx]
    else:
        return "\0"

reservedWords = ["if", "else", "for", "while", "return", "asm"]
typeWords = ["int", "uint", "bool", "void"]
opChars = ["+", "-", "*", "/", "%", "|", "&", "^"]
spOpChars = ["!", "~"] #only one input instead of two

whitespace = [" ", "\t"]
newline = ["\n"]
nameChars = list(string.ascii_letters)
nameChars.append("_")
nameStartChars = nameChars[:]
nameChars.extend(string.digits)
numberChars = list(string.digits)
numberChars.append(".")

program = []

#TODO: short assign
#TODO: strip comments

i = 0
while i < len(code):
    char = sread(i)
    if char in whitespace or char in newline:
        i += 1
    elif char in nameStartChars:
        s = i
        while sread(i) in nameChars:
            i += 1
        val = code[s:i]
        
        if val == "true" or val == "false":
            program.append(Symbol("bool", val))
        elif val in reservedWords:
            program.append(Symbol("rword", val))
        elif val in typeWords:
            program.append(Symbol("tword", val))
        else:
            program.append(Symbol("name", val))
    elif char in numberChars:
        s = i
        while sread(i) in numberChars:
            i += 1
        val = code[s:i]
        
        program.append(Symbol("number", int(val)))
    elif char == "(":
        program.append(Symbol("lparen"))
        i += 1
    elif char == ")":
        program.append(Symbol("rparen"))
        i += 1
    elif char == "[":
        program.append(Symbol("lbracket"))
        i += 1
    elif char == "]":
        program.append(Symbol("rbracket"))
        i += 1
    elif char == "{":
        program.append(Symbol("lbrace"))
        i += 1
        #ASM code includes
        if program[len(program) - 2].type == "rword" and program[len(program) - 2].value == "asm":
            del program[len(program) - 1]
            del program[len(program) - 1]
            
            s = i
            while sread(i) != "}":
                i += 1
            asm = code[s:i]
            i += 1
            
            program.append(Symbol("asm", asm))
    elif char == "}":
        program.append(Symbol("rbrace"))
        i += 1
    elif char == "=":
        if sread(i + 1) == "=":
            program.append(Symbol("op", "==", "compare"))
            i += 2
        else:
            program.append(Symbol("assign"))
            i += 1
    elif char == "<":
        if sread(i + 1) == "=":
            program.append(Symbol("op", "<=", "compare"))
            i += 2
        else:
            program.append(Symbol("op", "<", "compare"))
            i += 1
    elif char == ">":
        if sread(i + 1) == "=":
            program.append(Symbol("op", ">=", "compare"))
            i += 2
        else:
            program.append(Symbol("op", ">", "compare"))
            i += 1
    elif char == "!":
        if sread(i + 1) == "=":
            program.append(Symbol("op", "!=", "compare"))
            i += 2
        else:
            program.append(Symbol("spop", char))
            i += 1
    elif char in opChars:
        if char == "&" and sread(i + 1) == "&":
            program.append(Symbol("op", "&&"))
            i += 2
        elif char == "|" and sread(i + 1) == "|":
            program.append(Symbol("op", "||"))
            i += 2
        else:
            program.append(Symbol("op", char))
            i += 1
    elif char in spOpChars:
        program.append(Symbol("spop", char))
        i += 1
    elif char == ";":
        program.append(Symbol("semicolon"))
        i += 1
    elif char == ",":
        program.append(Symbol("comma"))
        i += 1
    elif char == "\"":
        #TODO: escaped quotes
        i += 1
        s = i
        while sread(i) != "\"":
            i += 1
        val = code[s:i]
        i += 1
        
        program.append(Symbol("string", val))
    elif char == "'" and sread(i + 1) != "'" and sread(i + 2) == "'":
        c = sread(i + 1)
        program.append(Symbol("number", ord(c)))
        i += 3

programPre = program

pgEnd = 0
def getParenGroup(symbols, i, ltype, rtype):
    global pgEnd
    pCount = 1 #number of parentheses - left is +1, right is -1
    start = i
    while pCount > 0: #TODO: throw error if matching paren is missing
        i += 1
        if symbols[i].type == ltype:
            pCount += 1
        elif symbols[i].type == rtype:
            pCount -= 1
    
    _pgEnd = i
    
    symbols2 = processSubgroup(symbols[start + 1:_pgEnd])
    pgEnd = _pgEnd #FIXME - use return value instead
    
    out = []
    i = 0
    s = i
    while i < len(symbols2):
        if symbols2[i].type == "comma":
            out.append(symbols2[s:i])
            s = i + 1
        i += 1
    out.append(symbols2[s:])
    
    return out

def processSubgroup(symbols):
    program = []
    i = 0
    while i < len(symbols):
        sym = symbols[i]
        if sym.type == "lparen":
            program.append(Symbol("paren", getParenGroup(symbols, i, "lparen", "rparen")))
            i = pgEnd + 1
        elif sym.type == "lbracket":
            program.append(Symbol("bracket", getParenGroup(symbols, i, "lbracket", "rbracket")))
            i = pgEnd + 1
        elif sym.type == "lbrace":
            program.append(Symbol("brace", getParenGroup(symbols, i, "lbrace", "rbrace")))
            i = pgEnd + 1
        else:
            program.append(sym)
            i += 1
    return program

program = processSubgroup(programPre)

#END PREPROCESSOR
header = []

def getTypeSize(t):
    if t == "int" or t == "uint":
        return FLAG_WORD_SIZE
    elif t == "bool":
        return FLAG_WORD_SIZE #TODO: only one byte
    elif t == "void":
        return 0 #FIXME
    else:
        raise ValueError("Invalid variable type.") #TODO: is this the correct exception type?

class ASM:
    op = None
    a = None
    b = None
    q = None
    jmpTo = None
    jmpFrom = None
    
    def __init__(self, _op, _a = 0, _b = 0, _q = 0, **kwargs):
        self.op = _op
        self.a = _a
        self.b = _b
        self.q = _q
        
        self.jmpTo = None
        self.jmpFrom = None
        if "jmpTo" in kwargs:
            self.jmpTo = kwargs["jmpTo"]
        if "jmpFrom" in kwargs:
            self.jmpFrom = kwargs["jmpFrom"]
    
    def __repr__(self):
        return "%s %d %d > %d" % (self.op, self.a, self.b, self.q)
    
    def tostr(self):
        return "%s %d %d %d" % (self.op, self.a, self.b, self.q)

class Var:
    name = None
    type = None #int, uint, bool
    ptr = None
    mmapR = None
    isGlobal = False
    arraySize = 0
    isArray = False
    itemSize = FLAG_WORD_SIZE
    
    def __init__(self, mmap, _name, _type, _isGlobal = False, _arraySize = 0):
        self.name = _name
        self.type = _type
        self.arraySize = _arraySize
        self.itemSize = getTypeSize(self.type)
        if self.arraySize == 0:
            self.ptr = alloc(mmap, self.itemSize)
            self.isArray = False
        else:
            self.ptr = alloc(mmap, self.itemSize * self.arraySize)
            self.isArray = True
        self.mmapR = mmap
        self.isGlobal = _isGlobal
    
    def __del__(self):
        dealloc(self.mmapR, self.ptr)
    
    def __repr__(self):
        return "{name: %s, type: %s, ptr: %d}" % (self.name, self.type, self.ptr)
    
    def getArrayPtr(self, arrayIndex):
        return self.ptr + (arrayIndex * self.itemSize)

def parseArrayRef(vars, symbols):
    name = symbols[0].value
    if len(symbols[1].value) != 1:
        raise Exception("Error") #FIXME
    if len(symbols[1].value[0]) != 1:
        raise Exception("Error") #FIXME
    if symbols[1].value[0][0].type != "number":
        raise Exception("Error") #FIXME
    arrayIndex = symbols[1].value[0][0].value
    
    var = getvar(vars, name)
    if not var.isArray:
        raise Exception("variable is not an array") #FIXME
    
    return var.getArrayPtr(arrayIndex)

#REGISTERS:
#  r0 is flags
#  r1 is stack pointer
#  r2 is global stack pointer
#  r4-r7 are generic

FLAG_SPTR = 1 #reg for stack pointer
FLAG_GSPTR = 2 #reg for global stack pointer
FLAG_GREG = 4 #start of generic registers

def alloc(mmap, size):
    i = 0
    fc = 0
    while True:
        if i >= len(mmap):
            mmap.append(0)
        if mmap[i] == 0:
            fc += 1
        else:
            fc = 0
        if fc >= size:
            i -= fc - 1
            ptr = i
            for n in range(fc):
                mmap[i] = fc - n
                i += 1
            return ptr
        
        i += 1

def dealloc(mmap, ptr):
    i = ptr
    c = mmap[i]
    for n in range(c):
        mmap[i] = 0
        i += 1

def getMmapTop(mmap):
    top = 0
    for i in range(len(mmap)):
        if mmap[i] != 0:
            top = i + 1
    return top

def getPtrSize(mmap, ptr):
    i = ptr
    c = mmap[i]
    return c

#---FUNCTIONS---

class Function:
    name = ""
    jmpTag = -1
    argMap = []
    retSize = 0
    def __init__(self, _name, _jmpTag, _argMap = [], _retSize = 0):
        self.name = _name
        self.jmpTag = _jmpTag
        self.argMap = _argMap
        self.retSize = _retSize

func = []

def isFunc(name):
    for f in func:
        if f.name == name:
            return True
    return False

def getFunc(name):
    for f in func:
        if f.name == name:
            return f
    return None

#Function args are an array of pointers
def runFunc(mmap, name, args, outptr):
    f = getFunc(name)
    out = []
    out.extend(const(getMmapTop(mmap), FLAG_GREG + 1)) #location of new stack relative to old stack
    out.append(ASM("add", FLAG_GREG + 1, FLAG_SPTR, FLAG_GREG)) #add to old stack to get absolute memory address
    out.append(ASM("stor", FLAG_SPTR, FLAG_GREG)) #store old stack pointer at bottom of new stack
    moffset = FLAG_WORD_SIZE * 3 #leave space for the return address and return value pointer
    #TODO use f.argMap
    for i in range(len(args)):
        #put args at the bottom of the new stack
        out.extend(const(args[i], FLAG_GREG + 2))
        out.append(ASM("add", FLAG_GREG + 2, FLAG_SPTR, FLAG_GREG + 1)) #source address in GREG+1
        out.extend(const(moffset, FLAG_GREG + 3))
        out.append(ASM("add", FLAG_GREG, FLAG_GREG + 3, FLAG_GREG + 3)) #target address in GREG+3
        
        size = math.ceil(getPtrSize(mmap, args[i]) / FLAG_WORD_SIZE)
        for i in range(size):
            out.append(ASM("load", 0, FLAG_GREG + 1, FLAG_GREG + 2)) #address in GREG+1, loaded word into GREG+2
            out.append(ASM("stor", FLAG_GREG + 2, FLAG_GREG + 3, 0)) #store word in target address (GREG+3)
            moffset += FLAG_WORD_SIZE
            if i < size:
                out.extend(const(FLAG_WORD_SIZE, FLAG_GREG + 2))
                out.append(ASM("add", FLAG_GREG + 2, FLAG_GREG + 1, FLAG_GREG + 1)) #increment source address
                out.append(ASM("add", FLAG_GREG + 2, FLAG_GREG + 3, FLAG_GREG + 3)) #increment target address
    out.append(ASM("copy", FLAG_GREG, 0, FLAG_SPTR)) #update stack pointer
    
    #return address
    ret = getJumpTag()
    out.append(ASM("chigh", 0, 0, FLAG_GREG, jmpTo = ret))
    out.append(ASM("clow", 0, 0, FLAG_GREG, jmpTo = ret))
    out.extend(const(FLAG_WORD_SIZE, FLAG_GREG + 1))
    out.append(ASM("add", FLAG_GREG + 1, FLAG_SPTR, FLAG_GREG + 1))
    out.append(ASM("stor", FLAG_GREG, FLAG_GREG + 1, 0))
    
    #jump to function
    out.append(ASM("chigh", 0, 0, FLAG_GREG, jmpTo = f.jmpTag))
    out.append(ASM("clow", 0, 0, FLAG_GREG, jmpTo = f.jmpTag))
    out.append(ASM("jmp", 0, FLAG_GREG, 0))
    
    out.append(ASM("noop", jmpFrom = ret))
    
    #put the function's stack pointer in GREG+0 and restore the old one
    out.append(ASM("copy", FLAG_SPTR, 0, FLAG_GREG))
    out.append(ASM("load", 0, FLAG_GREG, FLAG_SPTR))
    
    #upon return, copy from the return pointer (function sptr+WORD_SIZE*2) to the outptr
    if f.retSize > 0:
        out.extend(const(FLAG_WORD_SIZE * 2, FLAG_GREG + 2))
        out.append(ASM("add", FLAG_GREG + 2, FLAG_GREG, FLAG_GREG + 2)) #pointer to pointer in GREG+2
        out.append(ASM("load", 0, FLAG_GREG + 2, FLAG_GREG + 1)) #source address in GREG+1
        out.extend(const(outptr, FLAG_GREG + 3))
        out.append(ASM("add", FLAG_SPTR, FLAG_GREG + 3, FLAG_GREG + 3)) #target address in GREG+3
        
        size = math.ceil(f.retSize / FLAG_WORD_SIZE)
        for i in range(size):
            out.append(ASM("load", 0, FLAG_GREG + 1, FLAG_GREG + 2)) #address in GREG+1, loaded word into GREG+2
            out.append(ASM("stor", FLAG_GREG + 2, FLAG_GREG + 3, 0)) #store word in target address (GREG+3)
            if i < size:
                out.extend(const(FLAG_WORD_SIZE, FLAG_GREG + 2))
                out.append(ASM("add", FLAG_GREG + 2, FLAG_GREG + 1, FLAG_GREG + 1)) #increment source address
                out.append(ASM("add", FLAG_GREG + 2, FLAG_GREG + 3, FLAG_GREG + 3)) #increment target address
    
    return out

#---END FUNCTIONS---

asm = []
jmpOff = 0

def getJumpTag():
    global jmpOff
    j = jmpOff
    jmpOff += 1
    return j

def const(number, reg):
    out = []
    out.append(ASM("chigh", (number >> 24) & 255, (number >> 16) & 255, reg))
    out.append(ASM("clow", (number >> 8) & 255, number & 255, reg))
    return out

def getvar(vars, name):
    for var in vars:
        if var.name == name:
            return var

#TODO: global arrays

namenumber = ["name", "number", "ptr"]
def subexpr(mmap, vars, tmp, expr, outptr):
    out = []
    
    if len(expr) == 1 and expr[0].type in namenumber:
        if expr[0].type == "number":
            out.extend(const(expr[0].value, FLAG_GREG))
            out.extend(const(outptr, FLAG_GREG + 1))
            out.append(ASM("add", FLAG_GREG + 1, FLAG_SPTR, FLAG_GREG + 2))
            out.append(ASM("stor", FLAG_GREG, FLAG_GREG + 2))
        elif expr[0].type == "name":
            name = expr[0].value
            #if name in vars:
            var = getvar(vars, name)
            out.extend(const(var.ptr, FLAG_GREG))
            if var.isGlobal:
                out.append(ASM("add", FLAG_GREG, FLAG_GSPTR, FLAG_GREG + 2))
            else:
                out.append(ASM("add", FLAG_GREG, FLAG_SPTR, FLAG_GREG + 2))
            if hasattr(expr[0], "indirectOffset"):
                out.extend(const(expr[0].indirectOffset, FLAG_GREG))
                out.append(ASM("add", FLAG_GREG, FLAG_SPTR, FLAG_GREG))
                out.append(ASM("load", 0, FLAG_GREG, FLAG_GREG))
                out.append(ASM("add", FLAG_GREG, FLAG_GREG + 2, FLAG_GREG + 2))
            out.append(ASM("load", 0, FLAG_GREG + 2, FLAG_GREG + 1))
            out.extend(const(outptr, FLAG_GREG))
            out.append(ASM("add", FLAG_GREG, FLAG_SPTR, FLAG_GREG + 2))
            out.append(ASM("stor", FLAG_GREG + 1, FLAG_GREG + 2))
            #else:
            #    raise Exception("Variable not found") #FIXME
        elif expr[0].type == "ptr":
            ptr = expr[0].value
            out.extend(const(ptr, FLAG_GREG))
            out.append(ASM("add", FLAG_GREG, FLAG_SPTR, FLAG_GREG + 2))
            out.append(ASM("load", 0, FLAG_GREG + 2, FLAG_GREG + 1))
            out.extend(const(outptr, FLAG_GREG))
            out.append(ASM("add", FLAG_GREG, FLAG_SPTR, FLAG_GREG + 2))
            out.append(ASM("stor", FLAG_GREG + 1, FLAG_GREG + 2))
    elif len(expr) == 2 and expr[0].type == "spop" and expr[1].type in namenumber:
        if expr[1].type == "name":
            name = expr[1].value
            var = getvar(vars, name)
            out.extend(const(var.ptr, FLAG_GREG + 1))
            if var.isGlobal:
                out.append(ASM("add", FLAG_GREG + 1, FLAG_GSPTR, FLAG_GREG + 2))
            else:
                out.append(ASM("add", FLAG_GREG + 1, FLAG_SPTR, FLAG_GREG + 2))
            if hasattr(expr[1], "indirectOffset"):
                out.extend(const(expr[1].indirectOffset, FLAG_GREG))
                out.append(ASM("add", FLAG_GREG, FLAG_SPTR, FLAG_GREG))
                out.append(ASM("load", 0, FLAG_GREG, FLAG_GREG))
                out.append(ASM("add", FLAG_GREG, FLAG_GREG + 2, FLAG_GREG + 2))
            out.append(ASM("load", 0, FLAG_GREG + 2, FLAG_GREG))
        elif expr[1].type == "number":
            out.extend(const(expr[1].value, FLAG_GREG))
        elif expr[1].type == "ptr":
            ptr = expr[1].value
            out.extend(const(ptr, FLAG_GREG + 1))
            out.append(ASM("add", FLAG_GREG + 1, FLAG_SPTR, FLAG_GREG + 2))
            out.append(ASM("load", 0, FLAG_GREG + 2, FLAG_GREG))
        else:
            raise Exception("Invalid syntax") #FIXME
        
        if expr[0].value == "!":
            out.append(ASM("not", FLAG_GREG, 0, FLAG_GREG + 2))
            out.extend(const(1, FLAG_GREG))
            out.append(ASM("and", FLAG_GREG + 2, FLAG_GREG, FLAG_GREG + 1))
        elif expr[0].value == "~":
            out.append(ASM("not", FLAG_GREG, 0, FLAG_GREG + 1))
        else:
            raise Exception("Invalid spop")
        
        out.extend(const(outptr, FLAG_GREG))
        out.append(ASM("add", FLAG_GREG, FLAG_SPTR, FLAG_GREG + 2))
        out.append(ASM("stor", FLAG_GREG + 1, FLAG_GREG + 2))
    elif len(expr) == 3 and expr[0].type in namenumber and expr[1].type == "op" and expr[2].type in namenumber:
        if expr[0].type == "name":
            name = expr[0].value
            var = getvar(vars, name)
            out.extend(const(var.ptr, FLAG_GREG + 1))
            if var.isGlobal:
                out.append(ASM("add", FLAG_GREG + 1, FLAG_GSPTR, FLAG_GREG + 2))
            else:
                out.append(ASM("add", FLAG_GREG + 1, FLAG_SPTR, FLAG_GREG + 2))
            if hasattr(expr[0], "indirectOffset"):
                out.extend(const(expr[0].indirectOffset, FLAG_GREG))
                out.append(ASM("add", FLAG_GREG, FLAG_SPTR, FLAG_GREG))
                out.append(ASM("load", 0, FLAG_GREG, FLAG_GREG))
                out.append(ASM("add", FLAG_GREG, FLAG_GREG + 2, FLAG_GREG + 2))
            out.append(ASM("load", 0, FLAG_GREG + 2, FLAG_GREG))
        elif expr[0].type == "number":
            out.extend(const(expr[0].value, FLAG_GREG))
        elif expr[0].type == "ptr":
            ptr = expr[0].value
            out.extend(const(ptr, FLAG_GREG + 1))
            out.append(ASM("add", FLAG_GREG + 1, FLAG_SPTR, FLAG_GREG + 2))
            out.append(ASM("load", 0, FLAG_GREG + 2, FLAG_GREG))
        else:
            raise Exception("Invalid syntax") #FIXME
        
        if expr[2].type == "name":
            name = expr[2].value
            var = getvar(vars, name)
            out.extend(const(var.ptr, FLAG_GREG + 2))
            if var.isGlobal:
                out.append(ASM("add", FLAG_GREG + 2, FLAG_GSPTR, FLAG_GREG + 3))
            else:
                out.append(ASM("add", FLAG_GREG + 2, FLAG_SPTR, FLAG_GREG + 3))
            if hasattr(expr[2], "indirectOffset"):
                out.extend(const(expr[2].indirectOffset, FLAG_GREG))
                out.append(ASM("add", FLAG_GREG + 1, FLAG_SPTR, FLAG_GREG + 1))
                out.append(ASM("load", 0, FLAG_GREG + 1, FLAG_GREG + 1))
                out.append(ASM("add", FLAG_GREG + 1, FLAG_GREG + 3, FLAG_GREG + 3))
            out.append(ASM("load", 0, FLAG_GREG + 3, FLAG_GREG + 1))
        elif expr[2].type == "number":
            out.extend(const(expr[2].value, FLAG_GREG + 1))
        elif expr[2].type == "ptr":
            ptr = expr[2].value
            out.extend(const(ptr, FLAG_GREG + 2))
            out.append(ASM("add", FLAG_GREG + 2, FLAG_SPTR, FLAG_GREG + 3))
            out.append(ASM("load", 0, FLAG_GREG + 3, FLAG_GREG + 1))
        else:
            raise Exception("Invalid syntax") #FIXME
        
        #["+", "-", "*", "/", "%", "|", "&", "^"] && ||
        op = expr[1].value
        if op == "+":
            out.append(ASM("add", FLAG_GREG, FLAG_GREG + 1, FLAG_GREG + 2))
        elif op == "-":
            #convert FLAG_GREG + 1 to two's comp then add
            #TODO
            pass
        elif op == "*":
            #TODO
            pass
        elif op == "/":
            #TODO
            pass
        elif op == "%":
            #TODO
            pass
        elif op == "|":
            out.append(ASM("or", FLAG_GREG, FLAG_GREG + 1, FLAG_GREG + 2))
        elif op == "&":
            out.append(ASM("and", FLAG_GREG, FLAG_GREG + 1, FLAG_GREG + 2))
        elif op == "^":
            out.append(ASM("xor", FLAG_GREG, FLAG_GREG + 1, FLAG_GREG + 2))
        elif op == "&&": #FIXME
            out.append(ASM("and", FLAG_GREG, FLAG_GREG + 1, FLAG_GREG + 3))
            out.extend(const(1, FLAG_GREG))
            out.append(ASM("and", FLAG_GREG, FLAG_GREG + 3, FLAG_GREG + 2))
        elif op == "||": #FIXME
            out.append(ASM("or", FLAG_GREG, FLAG_GREG + 1, FLAG_GREG + 3))
            out.extend(const(1, FLAG_GREG))
            out.append(ASM("and", FLAG_GREG, FLAG_GREG + 3, FLAG_GREG + 2))
        elif op == "==":
            out.append(ASM("eq", FLAG_GREG, FLAG_GREG + 1, FLAG_GREG + 2))
        elif op == ">":
            out.append(ASM("gt", FLAG_GREG, FLAG_GREG + 1, FLAG_GREG + 2))
        elif op == "<":
            out.append(ASM("gt", FLAG_GREG + 1, FLAG_GREG, FLAG_GREG + 2))
        elif op == ">=":
            out.append(ASM("copy", FLAG_GREG + 1, 0, FLAG_GREG + 2)) #FIXME
            out.append(ASM("gt", FLAG_GREG, FLAG_GREG + 2, FLAG_GREG + 1))
            out.append(ASM("eq", FLAG_GREG, FLAG_GREG + 2, FLAG_GREG + 3))
            out.append(ASM("or", FLAG_GREG + 1, FLAG_GREG + 3, FLAG_GREG + 2))
        elif op == "<=":
            out.append(ASM("copy", FLAG_GREG + 1, 0, FLAG_GREG + 2)) #FIXME
            out.append(ASM("gt", FLAG_GREG + 2, FLAG_GREG, FLAG_GREG + 1))
            out.append(ASM("eq", FLAG_GREG, FLAG_GREG + 2, FLAG_GREG + 3))
            out.append(ASM("or", FLAG_GREG + 1, FLAG_GREG + 3, FLAG_GREG + 2))
        #TODO: all ops --------------------------------------------------------------------------------------------------------------------------------------------------------------------------IMPORTANT TODO
        
        out.extend(const(outptr, FLAG_GREG))
        out.append(ASM("add", FLAG_GREG, FLAG_SPTR, FLAG_GREG + 1))
        out.append(ASM("stor", FLAG_GREG + 2, FLAG_GREG + 1))
    else:
        #more complex expressions, functions, parenthesis
        
        #look for functions
        i = 0
        while True: #len(expr) may change
            if expr[i].type == "name" and len(expr) > i + 1 and expr[i + 1].type == "paren": # and isFunc(expr[i].value):
                #found a function!
                if i + 1 >= len(expr):
                    raise Exception("Invalid syntax") #FIXME
                if expr[i + 1].type != "paren":
                    raise Exception("Invalid syntax") #FIXME
                
                if not isFunc(expr[i].value):
                    raise Exception("Function doesn't exist") #FIXME
                
                params = expr[i + 1].value
                
                #NOTE: if the expression is just a function, this is inefficient. it will reduce the expr to a pointer, and the subexpression parser will copy that pointer to the outptr
                paramPtr = []
                for n in range(len(params)):
                    if len(params[n]) == 0:
                        continue
                    
                    ptr = alloc(mmap, FLAG_WORD_SIZE) #TODO: be aware of data types
                    paramPtr.append(ptr)
                    tmp.append(ptr)
                    
                    out.extend(subexpr(mmap, vars, tmp, params[n], ptr))
                
                outptr2 = alloc(mmap, FLAG_WORD_SIZE)
                tmp.append(outptr2)
                
                out.extend(runFunc(mmap, expr[i].value, paramPtr, outptr2))
                
                expr[i] = Symbol("ptr", outptr2)
                del expr[i + 1]
                
                i += 1
            else:
                i += 1
            
            if i >= len(expr):
                break
        
        #look for parens
        i = 0
        while i < len(expr):
            if expr[i].type == "paren" or expr[i].type == "bracket":
                outptr2 = alloc(mmap, FLAG_WORD_SIZE)
                tmp.append(outptr2)
                
                out.extend(subexpr(mmap, vars, tmp, expr[i].value[0], outptr2))
                
                if expr[i].type == "paren":
                    expr[i] = Symbol("ptr", outptr2)
                elif expr[i].type == "bracket":
                    expr[i] = Symbol("arrayOffsetPtr", outptr2)
                
                i += 1
            else:
                i += 1
        
        #convert array names + offset pointers to "indirect" symbols
        i = 0
        while i < len(expr) - 1:
            if expr[i].type == "name" and expr[i + 1].type == "arrayOffsetPtr":
                expr[i].indirectOffset = expr[i + 1].value
                expr.pop(i + 1)
                i += 1
            else:
                i += 1
        
        if len(expr) <= 3:
            #expr should be ok - TODO: make sure
            out.extend(subexpr(mmap, vars, tmp, expr, outptr))
        else:
            #expr is too long - split
            #currently does right-to-left op ordering - TODO: PEMDAS
            
            if expr[0].type in namenumber and expr[1].type == "op":
                #put into a paren symbol
                p = expr[2:]
                expr = expr[0:2]
                expr.append(Symbol("paren", [p]))
                
                out.extend(subexpr(mmap, vars, tmp, expr, outptr))
            #TODO: exprs that start with a spop (and other forms?) ------------------------------------------------------------------------------------------------------------------------------IMPORTANT TODO
    return out

def parseExpr(mmap, vars, expr, outptr, tmp = None):
    sTmp = True
    if tmp == None:
        tmp = []
        sTmp = False
    out = []
    
    out = subexpr(mmap, vars, tmp, expr, outptr)
    
    if not sTmp:
        for ptr in tmp:
            dealloc(mmap, ptr)
    
    return out

#TODO: dealloc vars when exiting scope
def process(symbols, mmap = [], vars = [], isGlobal = False):
    asm = []
    #mmap = []
    #vars = []
    i = 0
    while i < len(symbols):
        #variable declaration
        if symbols[i].type == "tword" and symbols[i + 1].type == "name" and symbols[i + 2].type == "semicolon":
            type = symbols[i].value
            name = symbols[i + 1].value
            
            i += 3
            
            var = Var(mmap, name, type, isGlobal)
            vars.append(var) #TODO: scoping
        #array declaration
        elif symbols[i].type == "tword" and symbols[i + 1].type == "name" and symbols[i + 2].type == "bracket" and symbols[i + 3].type == "semicolon":
            type = symbols[i].value
            name = symbols[i + 1].value
            if len(symbols[i + 2].value) != 1:
                raise Exception("Error") #FIXME
            if len(symbols[i + 2].value[0]) != 1:
                raise Exception("Error") #FIXME
            if symbols[i + 2].value[0][0].type != "number":
                raise Exception("Error") #FIXME
            arraySize = symbols[i + 2].value[0][0].value
            
            i += 4
            
            var = Var(mmap, name, type, isGlobal, arraySize)
            vars.append(var) #TODO: scoping
        #variable declaration + assignment
        elif symbols[i].type == "tword" and symbols[i + 1].type == "name" and symbols[i + 2].type == "assign": #TODO: short assign expansion - preprocess?
            type = symbols[i].value
            name = symbols[i + 1].value
            i += 3
            s = i
            while symbols[i].type != "semicolon":
                i += 1
            expr = symbols[s:i]
            i += 1
            
            var = Var(mmap, name, type, isGlobal)
            vars.append(var) #TODO: scoping
            
            asm.extend(parseExpr(mmap, vars, expr, var.ptr))
        #TODO: array declaration + assignment
        #variable assignment
        elif symbols[i].type == "name" and symbols[i + 1].type == "assign": #TODO: short assign expansion - preprocess?
            name = symbols[i].value
            i += 2
            s = i
            while symbols[i].type != "semicolon":
                i += 1
            expr = symbols[s:i]
            i += 1
            
            var = getvar(vars, name)
            
            asm.extend(parseExpr(mmap, vars, expr, var.ptr))
        #array index assignment
        elif symbols[i].type == "name" and symbols[i + 1].type == "bracket" and symbols[i + 2].type == "assign":
            name = symbols[i].value
            iExpr = symbols[i + 1].value[0]
            indexPtr = alloc(mmap, FLAG_WORD_SIZE)
            asm.extend(parseExpr(mmap, vars, iExpr, indexPtr))
            
            var = getvar(vars, name)
            if not var.isArray:
                raise Exception("variable is not an array") #FIXME
            
            #add value at indexPtr to var.ptr and store as value at indexPtr
            asm.extend(const(indexPtr, FLAG_GREG))
            asm.append(ASM("add", FLAG_GREG, FLAG_SPTR, FLAG_GREG))
            asm.append(ASM("load", 0, FLAG_GREG, FLAG_GREG + 1))
            asm.extend(const(var.ptr, FLAG_GREG + 2))
            asm.append(ASM("add", FLAG_GREG + 2, FLAG_GREG + 1, FLAG_GREG + 1))
            asm.append(ASM("stor", FLAG_GREG + 1, FLAG_GREG, 0))
            
            ptr = alloc(mmap, FLAG_WORD_SIZE)
            
            i += 3
            s = i
            while symbols[i].type != "semicolon":
                i += 1
            expr = symbols[s:i]
            i += 1
            
            asm.extend(parseExpr(mmap, vars, expr, ptr))
            
            #put expression result in destination
            asm.extend(const(ptr, FLAG_GREG))
            asm.append(ASM("add", FLAG_GREG, FLAG_SPTR, FLAG_GREG))
            asm.append(ASM("load", 0, FLAG_GREG, FLAG_GREG + 1)) #value of expression in GREG+1
            asm.extend(const(indexPtr, FLAG_GREG))
            asm.append(ASM("add", FLAG_GREG, FLAG_SPTR, FLAG_GREG))
            asm.append(ASM("load", 0, FLAG_GREG, FLAG_GREG + 2))
            asm.append(ASM("add", FLAG_GREG + 2, FLAG_SPTR, FLAG_GREG))
            asm.append(ASM("stor", FLAG_GREG + 1, FLAG_GREG, 0))
            
            dealloc(mmap, ptr)
            dealloc(mmap, indexPtr)
        #if() {}
        elif (symbols[i].type == "rword" and symbols[i].value == "if") and symbols[i + 1].type == "paren" and symbols[i + 2].type == "brace":
            eptr = alloc(mmap, FLAG_WORD_SIZE)
            
            expr = symbols[i + 1].value[0]
            asm.extend(parseExpr(mmap, vars, expr, eptr))
            
            code = symbols[i + 2].value[0]
            
            jmpTrue = getJumpTag()
            jmpFalse = getJumpTag()
            asm.extend(const(eptr, FLAG_GREG + 1))
            asm.append(ASM("add", FLAG_GREG + 1, FLAG_SPTR, FLAG_GREG + 2))
            asm.append(ASM("load", 0, FLAG_GREG + 2, FLAG_GREG))
            asm.append(ASM("chigh", 0, 0, FLAG_GREG + 1, jmpTo = jmpTrue))
            asm.append(ASM("clow", 0, 0, FLAG_GREG + 1, jmpTo = jmpTrue))
            asm.append(ASM("branch", FLAG_GREG, FLAG_GREG + 1))
            asm.append(ASM("chigh", 0, 0, FLAG_GREG, jmpTo = jmpFalse))
            asm.append(ASM("clow", 0, 0, FLAG_GREG, jmpTo = jmpFalse))
            asm.append(ASM("jmp", 0, FLAG_GREG, 0))
            asm.append(ASM("noop", jmpFrom = jmpTrue)) #FIXME
            asm.extend(process(code, mmap, vars))
            asm.append(ASM("noop", jmpFrom = jmpFalse)) #FIXME
            
            dealloc(mmap, eptr)
            i += 3
        #while() {}
        elif (symbols[i].type == "rword" and symbols[i].value == "while") and symbols[i + 1].type == "paren" and symbols[i + 2].type == "brace":
            eptr = alloc(mmap, FLAG_WORD_SIZE)
            
            jmpLoop = getJumpTag()
            asm.append(ASM("noop", jmpFrom = jmpLoop)) #FIXME
            
            expr = symbols[i + 1].value[0]
            asm.extend(parseExpr(mmap, vars, expr, eptr))
            
            code = symbols[i + 2].value[0]
            
            jmpTrue = getJumpTag()
            jmpFalse = getJumpTag()
            asm.extend(const(eptr, FLAG_GREG + 1))
            asm.append(ASM("add", FLAG_GREG + 1, FLAG_SPTR, FLAG_GREG + 2))
            asm.append(ASM("load", 0, FLAG_GREG + 2, FLAG_GREG))
            asm.append(ASM("chigh", 0, 0, FLAG_GREG + 1, jmpTo = jmpTrue))
            asm.append(ASM("clow", 0, 0, FLAG_GREG + 1, jmpTo = jmpTrue))
            asm.append(ASM("branch", FLAG_GREG, FLAG_GREG + 1))
            asm.append(ASM("chigh", 0, 0, FLAG_GREG, jmpTo = jmpFalse))
            asm.append(ASM("clow", 0, 0, FLAG_GREG, jmpTo = jmpFalse))
            asm.append(ASM("jmp", 0, FLAG_GREG, 0))
            asm.append(ASM("noop", jmpFrom = jmpTrue)) #FIXME
            asm.extend(process(code, mmap, vars))
            asm.append(ASM("chigh", 0, 0, FLAG_GREG, jmpTo = jmpLoop))
            asm.append(ASM("clow", 0, 0, FLAG_GREG, jmpTo = jmpLoop))
            asm.append(ASM("jmp", 0, FLAG_GREG, 0))
            asm.append(ASM("noop", jmpFrom = jmpFalse)) #FIXME
            
            dealloc(mmap, eptr)
            i += 3
        elif symbols[i].type == "asm":
            #TODO: better system
            for line in symbols[i].value.split("\n"):
                line = line.lstrip()
                if len(line) == 0:
                    continue
                sects = line.split(" ")
                if len(sects) >= 1:
                    op = sects[0]
                    regA = 0
                    regB = 0
                    regQ = 0
                    if len(sects) >= 2:
                        regA = int(sects[1])
                    if len(sects) >= 3:
                        regB = int(sects[2])
                    if len(sects) >= 4:
                        regQ = int(sects[3])
                    asm.append(ASM(op, regA, regB, regQ))
            i += 1
        #function([paramA[, paramB[, paramC...]]])
        elif symbols[i].type == "name" and len(symbols) > i + 1 and symbols[i + 1].type == "paren": # and isFunc(symbols[i].value):
            tmp = []
            #found a function!
            if i + 1 >= len(symbols):
                raise Exception("Invalid syntax") #FIXME
            if symbols[i + 1].type != "paren":
                raise Exception("Invalid syntax") #FIXME
            
            if not isFunc(symbols[i].value):
                raise Exception("Function doesn't exist") #FIXME
            
            params = symbols[i + 1].value
            paramPtr = []
            for n in range(len(params)):
                if len(params[n]) == 0:
                    continue
                
                ptr = alloc(mmap, FLAG_WORD_SIZE) #TODO: be aware of data types
                paramPtr.append(ptr)
                tmp.append(ptr)
                
                asm.extend(parseExpr(mmap, vars, params[n], ptr, tmp))
            
            outptr2 = alloc(mmap, FLAG_WORD_SIZE)
            tmp.append(outptr2)
            
            asm.extend(runFunc(mmap, symbols[i].value, paramPtr, outptr2))
            
            for ptr in tmp:
                dealloc(mmap, ptr)
            
            i += 2 #assume semicolon FIXME
        #tword functionName(params) {}
        elif symbols[i].type == "tword" and symbols[i + 1].type == "name" and symbols[i + 2].type == "paren" and symbols[i + 3].type == "brace":
            retType = symbols[i].value
            name = symbols[i + 1].value #TODO make sure name isn't in use
            params = symbols[i + 2].value
            code = symbols[i + 3].value[0]
            
            enterTag = getJumpTag()
            skipTag = getJumpTag()
            asm.append(ASM("chigh", 0, 0, FLAG_GREG, jmpTo = skipTag))
            asm.append(ASM("clow", 0, 0, FLAG_GREG, jmpTo = skipTag))
            asm.append(ASM("jmp", 0, FLAG_GREG, 0))
            asm.append(ASM("noop", jmpFrom = enterTag))
            
            localMmap = []
            for n in range(3): #old sptr, ret addr, return value pointer
                for nn in range(FLAG_WORD_SIZE):
                    localMmap.append(FLAG_WORD_SIZE - nn)
            localVars = []
            argMap = []
            
            for n in range(len(params)):
                param = params[n]
                if len(param) == 0:
                    pass
                elif len(param) == 2:
                    if param[0].type != "tword" or param[1].type != "name":
                        raise Exception("Invalid function declaration") #FIXME
                    var = Var(localMmap, param[1].value, param[0].value)
                    localVars.append(var)
                    argMap.append(getPtrSize(localMmap, var.ptr))
                else:
                    raise Exception("Error") #FIXME
            
            #return value
            retSize = getTypeSize(retType)
            retVar = None
            if retSize > 0:
                retVar = Var(localMmap, "__RETURN__", retType)
                localVars.append(retVar)
            
            #global variables
            for n in range(len(vars)):
                if vars[n].isGlobal:
                    localVars.append(vars[n])
            
            func.append(Function(name, enterTag, argMap, retSize)) #name, jmpTag, argMap, retSize
            
            asm.extend(process(code, localMmap, localVars))
            #return
            if retSize > 0:
                asm.extend(const(FLAG_WORD_SIZE * 2, FLAG_GREG)) #offset of return value pointer
                asm.append(ASM("add", FLAG_GREG, FLAG_SPTR, FLAG_GREG)) #calc absolute return pointer address
                
                asm.extend(const(retVar.ptr, FLAG_GREG + 1)) #retVar pointer
                asm.append(ASM("add", FLAG_GREG + 1, FLAG_SPTR, FLAG_GREG + 1)) #absolute retVar pointer
                asm.append(ASM("stor", FLAG_GREG + 1, FLAG_GREG, 0)) #put retVar pointer in the appropriate place
            asm.extend(const(FLAG_WORD_SIZE, FLAG_GREG)) #offset of return address
            asm.append(ASM("add", FLAG_GREG, FLAG_SPTR, FLAG_GREG)) #calc absolute return address
            asm.append(ASM("load", 0, FLAG_GREG, FLAG_GREG + 1)) #load return address
            asm.append(ASM("jmp", 0, FLAG_GREG + 1, 0)) #jump to return address

            asm.append(ASM("noop", jmpFrom = skipTag))

            i += 4
        elif (symbols[i].type == "rword" and symbols[i].value == "return"):
            #TODO: return from function (with return value)
            i += 1
            while symbols[i].type != "semicolon":
                i += 1
            i += 1
        else:
            i += 1
    
    return asm

startJumpTag = getJumpTag()
header.append(ASM("chigh", 0, 0, FLAG_GREG, jmpTo = startJumpTag))
header.append(ASM("clow", 0, 0, FLAG_GREG, jmpTo = startJumpTag))
header.append(ASM("jmp", 0, FLAG_GREG, 0))

testJumpTag = getJumpTag()
header.append(ASM("noop", jmpFrom = testJumpTag))
header.extend(const(0, FLAG_GREG))
header.extend(const(63, FLAG_GREG + 1))
header.append(ASM("busw", FLAG_GREG, FLAG_GREG + 1, 0))
#return
header.extend(const(FLAG_WORD_SIZE, FLAG_GREG))
header.append(ASM("add", FLAG_GREG, FLAG_SPTR, FLAG_GREG))
header.append(ASM("load", 0, FLAG_GREG, FLAG_GREG + 1))
header.append(ASM("jmp", 0, FLAG_GREG + 1, 0))

header.append(ASM("noop", jmpFrom = startJumpTag))

builtins = [
    Function("test", testJumpTag)
]
#func.extend(builtins)

asm = []
#asm.extend(header)
asm.extend(process(program, [], [], True))

#shutdown at end
asm.append(ASM("chigh", 0, 0, FLAG_GREG))
asm.append(ASM("clow", 0, 1, FLAG_GREG))
asm.append(ASM("chigh", 0, 0, FLAG_GREG + 1))
asm.append(ASM("clow", 0, 0, FLAG_GREG + 1))
asm.append(ASM("busw", FLAG_GREG, FLAG_GREG + 1, 0))

#stack pointer
sptr = (len(asm) + 3) * FLAG_ILEN
asm.insert(0, ASM("copy", FLAG_SPTR, 0, FLAG_GSPTR))
asm.insert(0, ASM("clow", (sptr >> 8) & 255, sptr & 255, FLAG_SPTR))
asm.insert(0, ASM("chigh", (sptr >> 24) & 255, (sptr >> 16) & 255, FLAG_SPTR))

#resolve jump tags
class Jump:
    id = 0
    target = 0
    def __init__(self, id, target):
        self.id = id
        self.target = target

jumps = []
for i in range(len(asm)):
    if asm[i].jmpFrom != None:
        jumps.append(Jump(asm[i].jmpFrom, i * FLAG_ILEN))

for i in range(len(asm)):
    if asm[i].jmpTo != None:
        for j in jumps:
            if asm[i].jmpTo == j.id:
                #match found
                if asm[i].op == "chigh":
                    asm[i].a = (j.target >> 24) & 255
                    asm[i].b = (j.target >> 16) & 255
                elif asm[i].op == "clow":
                    asm[i].a = (j.target >> 8) & 255
                    asm[i].b = j.target & 255
                break

for i in range(len(asm)):
    print(asm[i].tostr())
#*TODO: set stack pointer
#*TODO: postprocess jumps
