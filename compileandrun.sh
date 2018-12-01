#!/bin/bash
python3 compiler6.py $1 > asm.txt && python3 assembler.py asm.txt && python3 run.py program.bin
