/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

int * FUN_004a4c54(int *param_1,undefined4 param_2,undefined4 param_3)

{
  undefined4 uVar1;
  void *pvVar2;
  int *piVar3;
  int iVar4;
  int iVar5;
  uint uVar6;
  uint uVar7;
  int iVar8;
  undefined1 auStack_2c [4];
  undefined1 auStack_28 [4];
  undefined1 auStack_24 [4];
  undefined1 auStack_20 [4];
  undefined1 auStack_1c [8];
  
  uVar1 = DAT_004a4e50;
  param_1[0x30] = 0x5e715e28;
  FUN_0064a3fc(auStack_2c,uVar1);
  FUN_006c1630(auStack_28,DAT_004a4e54);
  FUN_0039173c(param_1,DAT_004a4e58,auStack_2c,0,auStack_28);
  FUN_006a0280(auStack_28);
  FUN_00627f38(auStack_2c);
  iVar4 = DAT_004a4e5c + 0x10c;
  iVar5 = DAT_004a4e5c + 0x134;
  iVar8 = DAT_004a4e5c + 0xfc;
  *param_1 = DAT_004a4e5c;
  param_1[0x25] = iVar4;
  param_1[0x26] = iVar5;
  param_1[0x1c] = iVar8;
  param_1[0x2c] = 0;
  param_1[0x2d] = 0;
  param_1[0x2e] = 0;
  iVar4 = FUN_004ad214(param_2,param_3,param_1 + 0x2b,param_1 + 0x2c);
  param_1[0x2f] = iVar4;
  FUN_0064a3fc(auStack_24,DAT_004a4e60);
  FUN_006c1630(auStack_20,DAT_004a4e54);
  FUN_006c1630(auStack_1c,DAT_004a4e54);
  pvVar2 = operator_new(0xd4);
  FUN_0038e434(pvVar2,auStack_24,auStack_20,auStack_1c);
  FUN_007ccc24(param_1,pvVar2,0xffffffff);
  FUN_006a0280(auStack_1c);
  FUN_006a0280(auStack_20);
  FUN_00627f38(auStack_24);
  if (param_1[0x2b] != 0) {
    FUN_007ccc24(param_1,param_1[0x2b],0xffffffff);
  }
  iVar4 = DAT_004a4e64;
  uVar6 = param_1[0x2e];
  if (0 < (int)uVar6) {
    uVar7 = 0;
    do {
      if (uVar7 < uVar6) {
        iVar5 = *(int *)(param_1[0x2c] + uVar7 * 4);
        if (iVar5 != 0) {
          FUN_007ccc24(param_1,iVar5,0xffffffff);
          piVar3 = *(int **)(param_1[0x2c] + uVar7 * 4);
          (**(code **)(*piVar3 + 0x28))(piVar3,iVar4 + uVar7 * 4);
          uVar6 = param_1[0x2e];
        }
      }
      uVar7 = uVar7 + 1;
    } while ((int)uVar7 < (int)uVar6);
  }
  return param_1;
}

