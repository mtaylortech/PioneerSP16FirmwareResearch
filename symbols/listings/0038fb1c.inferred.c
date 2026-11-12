/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_0038fb1c(int param_1,int *param_2,undefined4 param_3,undefined4 param_4,undefined4 param_5)

{
  undefined4 uVar1;
  int iVar2;
  int iVar3;
  undefined1 auStack_54 [16];
  undefined1 auStack_44 [4];
  undefined1 auStack_40 [4];
  undefined1 auStack_3c [4];
  undefined1 auStack_38 [4];
  undefined1 auStack_34 [4];
  undefined1 auStack_30 [4];
  undefined1 auStack_2c [4];
  undefined1 auStack_28 [4];
  undefined1 auStack_24 [8];
  
  (**(code **)(*param_2 + 0xc))(auStack_44);
  FUN_00620248(param_1 + 0x90,auStack_44);
  FUN_00627f38(auStack_44);
  (**(code **)(*param_2 + 8))(auStack_54,param_2,param_3);
  FUN_00627ba0(auStack_40,DAT_0038fd18);
  uVar1 = FUN_0068b048(auStack_54,auStack_40);
  FUN_006280c8(auStack_40);
  iVar2 = FUN_0061f6bc(uVar1);
  if (iVar2 == 0) {
    FUN_0061f85c(auStack_38,uVar1);
    FUN_00636894(auStack_34,auStack_38);
    FUN_00659dc8(auStack_3c,param_1 + 0x90,auStack_34);
    FUN_00627f38(auStack_38);
    iVar2 = FUN_00646364(auStack_3c);
    if (iVar2 != 0) {
      FUN_0070974c(auStack_30,auStack_3c);
      FUN_006d3310(param_1 + 0x88,auStack_30);
      FUN_00707778(auStack_30);
    }
    FUN_00627f38(auStack_3c);
  }
  FUN_00627ba0(auStack_2c,DAT_0038fd1c);
  uVar1 = FUN_0068b048(auStack_54,auStack_2c);
  FUN_006280c8(auStack_2c);
  iVar2 = FUN_0061f6bc(uVar1);
  if (iVar2 == 0) {
    FUN_0061f880(auStack_28,uVar1);
    uVar1 = FUN_00635d44(auStack_28);
    FUN_006c16fc(auStack_24,uVar1);
    FUN_006c1648(param_1 + 0x8c,auStack_24);
    FUN_006a0280(auStack_24);
    FUN_00627f38(auStack_28);
  }
  iVar2 = FUN_00760ee8(param_1);
  if (0 < iVar2) {
    iVar3 = 0;
    do {
      uVar1 = FUN_00760ef0(param_1,iVar3);
      FUN_0038f6c8(param_1,uVar1,param_2,auStack_54,param_4,param_5);
      iVar3 = iVar3 + 1;
    } while (iVar3 != iVar2);
  }
  FUN_0068d5a4(auStack_54);
  return;
}

