#!/bin/bash
python3 compiler2.py code.txt > asm.txt && python3 assembler.py asm.txt && python3 run.py program.bin
