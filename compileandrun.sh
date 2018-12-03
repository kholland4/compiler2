#!/bin/bash
python3 compiler7.py $1 > asm.txt && python3 assembler.py asm.txt && ./run.o
