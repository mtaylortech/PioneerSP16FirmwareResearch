/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_0038fd28(int *param_1,undefined4 param_2,undefined4 param_3,undefined4 param_4)

{
  undefined4 uVar1;
  int iVar2;
  int local_3c [4];
  undefined1 auStack_2c [4];
  undefined1 auStack_28 [4];
  undefined1 auStack_24 [4];
  undefined1 auStack_20 [4];
  undefined1 auStack_1c [4];
  undefined1 auStack_18 [4];
  undefined1 auStack_14 [4];
  
  FUN_00627ba0(auStack_2c,DAT_0038fed8);
  FUN_0068b1fc(local_3c,param_2,auStack_2c);
  FUN_006280c8(auStack_2c);
  if (local_3c[0] == 0) {
    FUN_004f782c(DAT_0038fee4,DAT_0038fee8,DAT_0038fef0);
  }
  else {
    FUN_00627b90(auStack_28);
    FUN_00627ba0(auStack_24,DAT_0038fedc);
    uVar1 = FUN_0068b048(local_3c,auStack_24);
    FUN_006280c8(auStack_24);
    iVar2 = FUN_0061f6bc(uVar1);
    if (iVar2 == 0) {
      FUN_0064a3fc(auStack_20,DAT_0038fee0);
      FUN_0061f85c(auStack_1c,uVar1);
      FUN_0062f808(auStack_18,auStack_20,auStack_1c);
      FUN_00663f10(auStack_14,auStack_18);
      FUN_0062abf4(auStack_28,auStack_14);
      FUN_006280c8(auStack_14);
      FUN_00627f38(auStack_18);
      FUN_00627f38(auStack_1c);
      FUN_00627f38(auStack_20);
      FUN_0038fb1c(param_1,param_4,auStack_28,0,0);
      (**(code **)(*param_1 + 0xdc))(param_1);
      FUN_006280c8(auStack_28);
      FUN_0068d5a4(local_3c);
      return;
    }
    FUN_004f782c(DAT_0038fee4,DAT_0038fee8,DAT_0038feec);
    FUN_006280c8(auStack_28);
  }
  FUN_0068d5a4(local_3c);
  return;
}

