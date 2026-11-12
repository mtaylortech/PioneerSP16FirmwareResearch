/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_0044c23c(int param_1,int param_2,undefined4 param_3,int param_4,undefined4 param_5,
                 undefined4 param_6,undefined4 param_7,undefined4 param_8,char *param_9,
                 undefined4 param_10,undefined4 param_11,undefined4 param_12,undefined4 param_13,
                 undefined4 param_14,char *param_15,int param_16)

{
  char cVar1;
  int *piVar2;
  char cVar3;
  int iVar4;
  int iVar5;
  int iVar6;
  uint in_fpscr;
  float fVar7;
  float fVar8;
  
  FUN_0044b994(param_1,param_2 != 0);
  FUN_0044ba78(param_1,param_2);
  FUN_0044bb6c(param_1,param_3);
  FUN_0044bf00(param_1,param_14);
  if (*(int *)(param_1 + 0x21c) != param_4) {
    piVar2 = *(int **)(param_1 + *(int *)(param_1 + 0x21c) * 4 + 0x1d4);
    (**(code **)(*piVar2 + 0x2c))(piVar2,0);
    piVar2 = *(int **)(param_1 + param_4 * 4 + 0x1d4);
    (**(code **)(*piVar2 + 0x2c))(piVar2,1);
    *(int *)(param_1 + 0x21c) = param_4;
  }
  FUN_0039dafc(*(undefined4 *)(param_1 + 0x184),param_5,param_6);
  FUN_0039dafc(*(undefined4 *)(param_1 + 0x188),param_7,param_8);
  FUN_0039dafc(*(undefined4 *)(param_1 + 0x18c),param_10,param_11);
  FUN_0039dafc(*(undefined4 *)(param_1 + 400),param_12,param_13);
  cVar1 = *param_9;
  if (*(char *)(param_1 + 0x220) == cVar1) {
    iVar6 = *(int *)(param_9 + 4);
    if (*(int *)(param_1 + 0x224) != iVar6) {
      iVar4 = *(int *)(param_9 + 8);
      iVar5 = *(int *)(param_9 + 0xc);
      cVar3 = param_9[0x10];
      goto LAB_0044c380;
    }
    iVar4 = *(int *)(param_9 + 8);
    if (*(int *)(param_1 + 0x228) != iVar4) {
      iVar5 = *(int *)(param_9 + 0xc);
      cVar3 = param_9[0x10];
      goto LAB_0044c380;
    }
    iVar5 = *(int *)(param_9 + 0xc);
    cVar3 = param_9[0x10];
    if (*(int *)(param_1 + 0x22c) != iVar5) goto LAB_0044c380;
    if (*(char *)(param_1 + 0x230) != cVar3) goto LAB_0044c380;
    iVar6 = FUN_0062e318(param_1 + 0x234,param_9 + 0x14);
    if ((iVar6 == 0) || (*(int *)(param_1 + 0x238) != *(int *)(param_9 + 0x18))) {
      cVar1 = *param_9;
      iVar6 = *(int *)(param_9 + 4);
      iVar4 = *(int *)(param_9 + 8);
      iVar5 = *(int *)(param_9 + 0xc);
      cVar3 = param_9[0x10];
      goto LAB_0044c380;
    }
  }
  else {
    iVar6 = *(int *)(param_9 + 4);
    iVar4 = *(int *)(param_9 + 8);
    iVar5 = *(int *)(param_9 + 0xc);
    cVar3 = param_9[0x10];
LAB_0044c380:
    *(char *)(param_1 + 0x220) = cVar1;
    *(int *)(param_1 + 0x228) = iVar4;
    *(char *)(param_1 + 0x230) = cVar3;
    *(int *)(param_1 + 0x224) = iVar6;
    *(int *)(param_1 + 0x22c) = iVar5;
    FUN_0062ab80(param_1 + 0x234,param_9 + 0x14);
    iVar6 = *(int *)(param_9 + 8);
    iVar4 = *(int *)(param_9 + 4);
    fVar7 = (float)VectorSignedToFloat(*(undefined4 *)(param_9 + 0xc),(byte)(in_fpscr >> 0x16) & 3);
    *(undefined4 *)(param_1 + 0x238) = *(undefined4 *)(param_9 + 0x18);
    fVar8 = (float)VectorSignedToFloat(iVar6 - iVar4,(byte)(in_fpscr >> 0x16) & 3);
    FUN_0079c798(*(undefined4 *)(param_1 + 0x17c),*(undefined4 *)(param_1 + 0x214),
                 0x177 - (int)((fVar7 / fVar8) * DAT_0044c6c0));
  }
  cVar1 = *param_15;
  if (*(char *)(param_1 + 0x23c) == cVar1) {
    iVar6 = *(int *)(param_15 + 4);
    if (*(int *)(param_1 + 0x240) == iVar6) {
      iVar4 = *(int *)(param_15 + 8);
      if (*(int *)(param_1 + 0x244) == iVar4) {
        iVar5 = *(int *)(param_15 + 0xc);
        cVar3 = param_15[0x10];
        if (*(int *)(param_1 + 0x248) == iVar5) {
          if (*(char *)(param_1 + 0x24c) == cVar3) {
            iVar6 = FUN_0062e318(param_1 + 0x250,param_15 + 0x14);
            if ((iVar6 != 0) && (*(int *)(param_1 + 0x254) == *(int *)(param_15 + 0x18)))
            goto LAB_0044c488;
            cVar1 = *param_15;
            iVar6 = *(int *)(param_15 + 4);
            iVar4 = *(int *)(param_15 + 8);
            iVar5 = *(int *)(param_15 + 0xc);
            cVar3 = param_15[0x10];
          }
        }
      }
      else {
        iVar5 = *(int *)(param_15 + 0xc);
        cVar3 = param_15[0x10];
      }
    }
    else {
      iVar4 = *(int *)(param_15 + 8);
      iVar5 = *(int *)(param_15 + 0xc);
      cVar3 = param_15[0x10];
    }
  }
  else {
    iVar6 = *(int *)(param_15 + 4);
    iVar4 = *(int *)(param_15 + 8);
    iVar5 = *(int *)(param_15 + 0xc);
    cVar3 = param_15[0x10];
  }
  *(char *)(param_1 + 0x23c) = cVar1;
  *(int *)(param_1 + 0x244) = iVar4;
  *(char *)(param_1 + 0x24c) = cVar3;
  *(int *)(param_1 + 0x240) = iVar6;
  *(int *)(param_1 + 0x248) = iVar5;
  FUN_0062ab80(param_1 + 0x250,param_15 + 0x14);
  iVar6 = *(int *)(param_15 + 8);
  iVar4 = *(int *)(param_15 + 4);
  fVar7 = (float)VectorSignedToFloat(*(undefined4 *)(param_15 + 0xc),(byte)(in_fpscr >> 0x16) & 3);
  *(undefined4 *)(param_1 + 0x254) = *(undefined4 *)(param_15 + 0x18);
  fVar8 = (float)VectorSignedToFloat(iVar6 - iVar4,(byte)(in_fpscr >> 0x16) & 3);
  FUN_0079c798(*(undefined4 *)(param_1 + 0x180),*(undefined4 *)(param_1 + 0x218),
               0x177 - (int)((fVar7 / fVar8) * DAT_0044c6c0));
LAB_0044c488:
  FUN_004a1ab8(*(undefined4 *)(param_1 + 0x194),param_16);
  FUN_004a1ab8(*(undefined4 *)(param_1 + 0x198),param_16 + 0x28);
  FUN_004a1ab8(*(undefined4 *)(param_1 + 0x19c),param_16 + 0x50);
  FUN_004a1ab8(*(undefined4 *)(param_1 + 0x1a0),param_16 + 0x78);
  FUN_004a1ab8(*(undefined4 *)(param_1 + 0x1a4),param_16 + 0xa0);
  FUN_004a1ab8(*(undefined4 *)(param_1 + 0x1a8),param_16 + 200);
  FUN_004a1ab8(*(undefined4 *)(param_1 + 0x1ac),param_16 + 0xf0);
  FUN_004a1ab8(*(undefined4 *)(param_1 + 0x1b0),param_16 + 0x118);
  FUN_004a1ab8(*(undefined4 *)(param_1 + 0x1b4),param_16 + 0x140);
  FUN_004a1ab8(*(undefined4 *)(param_1 + 0x1b8),param_16 + 0x168);
  FUN_004a1ab8(*(undefined4 *)(param_1 + 0x1bc),param_16 + 400);
  FUN_004a1ab8(*(undefined4 *)(param_1 + 0x1c0),param_16 + 0x1b8);
  FUN_004a1ab8(*(undefined4 *)(param_1 + 0x1c4),param_16 + 0x1e0);
  FUN_004a1ab8(*(undefined4 *)(param_1 + 0x1c8),param_16 + 0x208);
  FUN_004a1ab8(*(undefined4 *)(param_1 + 0x1cc),param_16 + 0x230);
  FUN_004a1ab8(*(undefined4 *)(param_1 + 0x1d0),param_16 + 600);
  return;
}

