#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <malloc.h>
#include <stdbool.h>

#define ILEN 4

unsigned char reg[16][4];
unsigned long busBuffer = 0;
unsigned char *mem;
unsigned char *disk;
long diskSize = 0;

unsigned long regread(unsigned char num) {
  return (((unsigned long)reg[num][0]) << 24) | (((unsigned long)reg[num][1]) << 16) | (((unsigned long)reg[num][2]) << 8) | ((unsigned long)reg[num][3]);
}

void regwrite(unsigned char num, unsigned long data) {
  reg[num][0] = (data >> 24) & 255;
  reg[num][1] = (data >> 16) & 255;
  reg[num][2] = (data >> 8) & 255;
  reg[num][3] = data & 255;
}

void busw(unsigned long addr, unsigned long data) {
  if(addr == 0) {
    putchar((char)(data & 255));
    fflush(stdout);
  } else if(addr == 1) {
    if(data == 0) {
      exit(0);
    }
  } else if(addr == 2) {
    if(data >= 0 && data < diskSize) {
      busBuffer = disk[data];
    }
  }
}

unsigned long busr() {
  return busBuffer;
}

int main(int argc, char *argv[]) {
  FILE *f = fopen("program.bin", "rb");
  fseek(f, 0, SEEK_END);
  long fsize = ftell(f);
  fseek(f, 0, SEEK_SET);
  
  mem = malloc(fsize + 65536);
  fread(mem, fsize, 1, f);
  fclose(f);
  
  FILE *diskF = fopen("data.img", "rb");
  fseek(diskF, 0, SEEK_END);
  diskSize = ftell(diskF);
  fseek(diskF, 0, SEEK_SET);
  
  disk = malloc(diskSize);
  fread(disk, diskSize, 1, diskF);
  fclose(diskF);
  
  unsigned long pos = 0;
  unsigned long offset = 0;
  while(pos + offset < fsize + 65536) {
    unsigned long iindex = pos + offset;
    unsigned char opcode = mem[iindex];
    unsigned char regA = mem[iindex + 1];
    unsigned char regB = mem[iindex + 2];
    unsigned char regQ = mem[iindex + 3];
    bool increment = true;
    
    switch(opcode) {
      case 0: //noop
        break;
      case 1: //chigh
        reg[regQ][0] = regA;
        reg[regQ][1] = regB;
        break;
      case 2: //clow
        reg[regQ][2] = regA;
        reg[regQ][3] = regB;
        break;
      case 3: //stor
        {
          unsigned long moffset = regread(regB);
          for(unsigned long i = 0; i < 4; i++) {
            mem[moffset + i] = reg[regA][i];
          }
        }
        break;
      case 4: //load
        {
          unsigned long moffset = regread(regB);
          for(unsigned long i = 0; i < 4; i++) {
            reg[regQ][i] = mem[moffset + i];
          }
        }
        break;
      case 5: //jmp
        pos = regread(regB);
        increment = false;
        break;
      case 6: //branch
        if(regread(regA) & 1 == 1) {
          pos = regread(regB);
          increment = false;
        }
        break;
      case 7: //local
        offset = regread(regA);
        pos = 0;
        increment = false;
        break;
      case 8: //busr
        regwrite(regQ, busr());
        break;
      case 9: //busw
        busw(regread(regA), regread(regB));
        break;
      case 128: //add
        regwrite(regQ, regread(regA) + regread(regB));
        break;
      case 129: //addc
        //TODO
        break;
      case 130: //and
        regwrite(regQ, regread(regA) & regread(regB));
        break;
      case 131: //or
        regwrite(regQ, regread(regA) | regread(regB));
        break;
      case 132: //not
        regwrite(regQ, ~regread(regA));
        break;
      case 133: //xor
        regwrite(regQ, regread(regA) ^ regread(regB));
        break;
      case 134: //eq
        regwrite(regQ, (unsigned long)(regread(regA) == regread(regB)));
        break;
      case 135: //gt
        regwrite(regQ, (unsigned long)(regread(regA) > regread(regB)));
        break;
      case 136: //bsl
        regwrite(regQ, regread(regA) << 1);
        break;
      case 137: //bsr
        regwrite(regQ, regread(regA) >> 1);
        break;
      case 138: //copy
        regwrite(regQ, regread(regA));
        break;
      default:
        break;
    }
    
    if(increment) {
      pos += ILEN;
    }
  }
}
