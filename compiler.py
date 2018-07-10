#!/usr/bin/python3
import sys, string, pickle

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
typeWords = ["int", "uint", "bool"]
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
    
    def __init__(self, mmap, _name, _type):
        self.name = _name
        self.type = _type
        if self.type == "int" or self.type == "uint":
            self.ptr = alloc(mmap, FLAG_WORD_SIZE)
        elif self.type == "bool":
            self.ptr = alloc(mmap, FLAG_WORD_SIZE) #TODO: only one byte
        else:
            raise ValueError("Invalid variable type.") #TODO: is this the correct exception type?
        self.mmapR = mmap
    
    def __del__(self):
        dealloc(self.mmapR, self.ptr)
    
    def __repr__(self):
        return "{name: %s, type: %s, ptr: %d}" % (self.name, self.type, self.ptr)

#TODO: arrays

#REGISTERS:
#  r0 is flags
#  r1 is global subroutine stack pointer
#  r2 is stack pointer
#  r3 is function stack pointer
#  r4-r7 are generic

FLAG_SPTR = 2
FLAG_GREG = 4

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

#---FUNCTIONS---

class Function:
    name = ""
    def __init__(self, _name):
        self.name = _name

func = []

def isFunc(name):
    for f in func:
        if f.name == name:
            return True
    return False

def runFunc(name, args, outptr):
    pass

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

namenumber = ["name", "number", "ptr"]
def subexpr(mmap, vars, tmp, expr, outptr):
    out = []
    
    if len(expr) == 1 and expr[0].type in namenumber:
        if expr[0].type == "number":
            out.extend(const(expr[0].value, FLAG_GREG))
            out.extend(const(outptr, FLAG_GREG + 1))
            out.append(ASM("stor", FLAG_GREG, FLAG_GREG + 1))
        elif expr[0].type == "name":
            name = expr[0].value
            #if name in vars:
            out.extend(const(getvar(vars, name).ptr, FLAG_GREG))
            out.append(ASM("load", 0, FLAG_GREG, FLAG_GREG + 1))
            out.extend(const(outptr, FLAG_GREG))
            out.append(ASM("stor", FLAG_GREG + 1, FLAG_GREG))
            #else:
            #    raise Exception("Variable not found") #FIXME
        elif expr[0].type == "ptr":
            ptr = expr[0].value
            out.extend(const(ptr, FLAG_GREG))
            out.append(ASM("load", 0, FLAG_GREG, FLAG_GREG + 1))
            out.extend(const(outptr, FLAG_GREG))
            out.append(ASM("stor", FLAG_GREG + 1, FLAG_GREG))
    elif len(expr) == 2 and expr[0].type == "spop" and expr[1].type in namenumber:
        if expr[1].type == "name":
            name = expr[1].value
            out.extend(const(getvar(vars, name).ptr, FLAG_GREG + 1))
            out.append(ASM("load", 0, FLAG_GREG + 1, FLAG_GREG))
        elif expr[1].type == "number":
            out.extend(const(expr[1].value, FLAG_GREG))
        elif expr[1].type == "ptr":
            ptr = expr[1].value
            out.extend(const(ptr, FLAG_GREG + 1))
            out.append(ASM("load", 0, FLAG_GREG + 1, FLAG_GREG))
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
        out.append(ASM("stor", FLAG_GREG + 1, FLAG_GREG))
    elif len(expr) == 3 and expr[0].type in namenumber and expr[1].type == "op" and expr[2].type in namenumber:
        if expr[0].type == "name":
            name = expr[0].value
            out.extend(const(getvar(vars, name).ptr, FLAG_GREG + 1))
            out.append(ASM("load", 0, FLAG_GREG + 1, FLAG_GREG))
        elif expr[0].type == "number":
            out.extend(const(expr[0].value, FLAG_GREG))
        elif expr[0].type == "ptr":
            ptr = expr[0].value
            out.extend(const(ptr, FLAG_GREG + 1))
            out.append(ASM("load", 0, FLAG_GREG + 1, FLAG_GREG))
        else:
            raise Exception("Invalid syntax") #FIXME
        
        if expr[2].type == "name":
            name = expr[2].value
            out.extend(const(getvar(vars, name).ptr, FLAG_GREG + 2))
            out.append(ASM("load", 0, FLAG_GREG + 2, FLAG_GREG + 1))
        elif expr[2].type == "number":
            out.extend(const(expr[2].value, FLAG_GREG + 1))
        elif expr[2].type == "ptr":
            ptr = expr[2].value
            out.extend(const(ptr, FLAG_GREG + 2))
            out.append(ASM("load", 0, FLAG_GREG + 2, FLAG_GREG + 1))
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
        out.append(ASM("stor", FLAG_GREG + 2, FLAG_GREG))
    else:
        #more complex expressions, functions, parenthesis
        
        #look for functions
        i = 0
        while True: #len(expr) may change
            if expr[i].type == "name" and isFunc(expr[i].value):
                #found a function!
                if i + 1 >= len(expr):
                    raise Exception("Invalid syntax") #FIXME
                if expr[i + 1] != "paren":
                    raise Exception("Invalid syntax") #FIXME
                
                params = expr[i + 1].value
                
                #NOTE: if the expression is just a function, this is inefficient. it will reduce the expr to a pointer, and the subexpression parser will copy that pointer to the outptr
                paramPtr = []
                for n in len(params):
                    ptr = alloc(mmap, FLAG_WORD_SIZE) #TODO: be aware of data types
                    paramPtr.append(ptr)
                    tmp.append(ptr)
                    
                    out.extend(subexpr(mmap, vars, tmp, params[n], ptr))
                
                outptr2 = alloc(mmap, FLAG_WORD_SIZE)
                tmp.append(outptr2)
                
                out.extend(runFunc(expr[i].value, paramPtr, outptr2))
                
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
            if expr[i].type == "paren":
                outptr2 = alloc(mmap, FLAG_WORD_SIZE)
                tmp.append(outptr2)
                
                out.extend(subexpr(mmap, vars, tmp, expr[i].value[0], outptr2))
                
                expr[i] = Symbol("ptr", outptr2)
                
                i += 1
            else:
                i += 1
        
        #TODO: array indices
        
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

def parseExpr(mmap, vars, expr, outptr):
    tmp = []
    out = []
    
    out = subexpr(mmap, vars, tmp, expr, outptr)
    
    for ptr in tmp:
        dealloc(mmap, ptr)
    
    return out

#TODO: dealloc vars when exiting scope
def process(symbols, mmap = [], vars = []):
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
            
            var = Var(mmap, name, type)
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
            
            var = Var(mmap, name, type)
            vars.append(var) #TODO: scoping
            
            asm.extend(parseExpr(mmap, vars, expr, var.ptr))
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
        #if() {}
        elif (symbols[i].type == "rword" and symbols[i].value == "if") and symbols[i + 1].type == "paren" and symbols[i + 2].type == "brace":
            eptr = alloc(mmap, FLAG_WORD_SIZE)
            
            expr = symbols[i + 1].value[0]
            asm.extend(parseExpr(mmap, vars, expr, eptr))
            
            code = symbols[i + 2].value[0]
            
            jmpTrue = getJumpTag()
            jmpFalse = getJumpTag()
            asm.extend(const(eptr, FLAG_GREG + 1))
            asm.append(ASM("load", 0, FLAG_GREG + 1, FLAG_GREG))
            asm.append(ASM("chigh", 0, 0, FLAG_GREG + 1, jmpTo = jmpTrue))
            asm.append(ASM("clow", 0, 0, FLAG_GREG + 1, jmpTo = jmpTrue))
            asm.append(ASM("branch", FLAG_GREG, FLAG_GREG + 1, 0))
            asm.append(ASM("chigh", 0, 0, FLAG_GREG, jmpTo = jmpFalse))
            asm.append(ASM("clow", 0, 0, FLAG_GREG, jmpTo = jmpFalse))
            asm.append(ASM("jmp", 0, FLAG_GREG, 0))
            asm.append(ASM("noop", jmpFrom = jmpTrue)) #FIXME
            asm.extend(process(code, mmap, vars))
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
        #TODO: function calls
        else:
            i += 1
    
    return asm

asm = process(program)

#shutdown at end
asm.append(ASM("chigh", 0, 0, FLAG_GREG))
asm.append(ASM("clow", 0, 1, FLAG_GREG))
asm.append(ASM("chigh", 0, 0, FLAG_GREG + 1))
asm.append(ASM("clow", 0, 0, FLAG_GREG + 1))
asm.append(ASM("busw", FLAG_GREG, FLAG_GREG + 1, 0))

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
#TODO: set stack pointer
#TODO: postprocess jumps
