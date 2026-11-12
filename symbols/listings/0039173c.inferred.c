/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

undefined4 *
FUN_0039173c(undefined4 *param_1,undefined4 *param_2,undefined4 param_3,int *param_4,
            undefined4 param_5)

{
  undefined4 uVar1;
  uint uVar2;
  int iVar3;
  undefined4 uVar4;
  undefined1 auStack_20 [4];
  undefined1 auStack_1c [4];
  
  FUN_00663f10(auStack_20,param_3);
  iVar3 = DAT_003918e8;
  FUN_006c1630(auStack_1c,param_5);
  FUN_00760bc8(param_1);
  uVar1 = DAT_003918ec;
  param_1[0x1d] = 0;
  param_1[0x1c] = uVar1;
  uVar1 = param_2[2];
  param_1[0x1c] = iVar3;
  param_1[0x1e] = 0;
  *param_1 = uVar1;
  param_1[0x1f] = 0;
  param_1[0x20] = 0;
  FUN_00627ba0(param_1 + 0x21,auStack_20);
  uVar4 = param_2[1];
  param_1[0x1c] = iVar3 + 0x16c;
  uVar1 = DAT_003918f0;
  *param_1 = uVar4;
  FUN_006d3148(param_1 + 0x22);
  FUN_006c1630(param_1 + 0x23,auStack_1c);
  FUN_0062ab08(param_1 + 0x24);
  FUN_006a0280(auStack_1c);
  FUN_006280c8(auStack_20);
  param_1[0x25] = uVar1;
  uVar1 = param_2[4];
  param_1[0x27] = param_4;
  param_1[0x26] = uVar1;
  if (param_4 != (int *)0x0) {
    if (((uint)param_4 & 3) == 0) {
      uVar2 = (int)param_4 + *(int *)(*param_4 + -0xc);
      if ((uVar2 != 0) && ((uVar2 & 3) == 0)) {
        if (*(int *)((int)param_4 + *(int *)(*param_4 + -0xc)) == 0x5e715e28) {
          FUN_0038d6e8(param_4,param_1 + 0x26);
          goto LAB_00391844;
        }
      }
    }
    FUN_004f782c(DAT_003918f8,DAT_003918fc,DAT_00391900);
    param_1[0x27] = 0;
  }
LAB_00391844:
  iVar3 = DAT_003918f4;
  uVar1 = param_2[3];
  param_1[0x28] = 0;
  param_1[0x26] = uVar1;
  uVar1 = *param_2;
  param_1[0x1c] = iVar3;
  param_1[0x25] = iVar3 + 0x10;
  *param_1 = uVar1;
  uVar1 = param_2[5];
  param_1[0x29] = 0;
  param_1[0x2a] = 0;
  param_1[0x26] = uVar1;
  FUN_00760d50(param_1,param_3);
  iVar3 = 1 - (int)param_4;
  if ((int *)0x1 < param_4) {
    iVar3 = 0;
  }
  FUN_00760eb0(param_1,1,iVar3);
  return param_1;
}

