/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_0026d170(int param_1)

{
  int iVar1;
  int iVar2;
  int iVar3;
  int *piVar4;
  undefined4 uVar5;
  code *pcVar6;
  undefined4 uVar7;
  undefined1 auStack_2c [4];
  undefined1 auStack_28 [4];
  undefined1 auStack_24 [4];
  undefined1 auStack_20 [4];
  undefined1 auStack_1c [8];
  
  *(undefined1 *)(param_1 + 0x6a8) = 0;
  iVar1 = (**(code **)(**(int **)(param_1 + 0x6ac) + 0x2c))();
  iVar2 = (**(code **)(**(int **)(param_1 + 0x6ac) + 0x3c))();
  FUN_0062ab08(auStack_2c);
  if (iVar1 == 0) {
    FUN_0062ab80(auStack_2c,DAT_0026d444);
  }
  else if ((iVar1 == 1) && (iVar3 = (**(code **)(**(int **)(param_1 + 0x6ac) + 0x34))(), -1 < iVar3)
          ) {
    if (iVar3 + 1 < *(int *)(param_1 + 0x6b8)) {
      FUN_0062ab80(auStack_2c,DAT_0026d444 + (iVar3 + 1) * 4);
    }
  }
  iVar3 = FUN_0062e318(DAT_0026d440,auStack_2c);
  if (iVar3 != 0) {
    FUN_0062ab80(auStack_2c,DAT_0026d444);
    FUN_004f7534(DAT_0026d448,DAT_0026d44c);
  }
  uVar7 = *(undefined4 *)(param_1 + 0x6b0);
  FUN_0062ab18(auStack_28,auStack_2c);
  FUN_001efe84(uVar7,0,auStack_28);
  FUN_00627f38(auStack_28);
  FUN_00627f38(auStack_2c);
  FUN_0062ab08(auStack_2c);
  if (iVar2 == 0) {
    FUN_0062ab80(auStack_2c,DAT_0026d450);
  }
  else if (iVar2 == 1) {
    FUN_0062ab80(auStack_2c,DAT_0026d454);
  }
  iVar2 = FUN_0062e318(DAT_0026d440,auStack_2c);
  if (iVar2 != 0) {
    FUN_0062ab80(auStack_2c,DAT_0026d450);
    FUN_004f7534(DAT_0026d448,DAT_0026d44c);
  }
  uVar7 = *(undefined4 *)(param_1 + 0x6b0);
  FUN_0062ab18(auStack_24,auStack_2c);
  FUN_001efe84(uVar7,1,auStack_24);
  FUN_00627f38(auStack_24);
  FUN_00627f38(auStack_2c);
  piVar4 = *(int **)(param_1 + 0x6b0);
  if (iVar1 == 0) {
    (**(code **)(*piVar4 + 0x3c))(piVar4,1,0);
    piVar4 = *(int **)(param_1 + 0x6b0);
    pcVar6 = *(code **)(*piVar4 + 0x34);
    FUN_006c1724(auStack_20,0x5a,0x61,0x6b);
    (*pcVar6)(piVar4,1,1,auStack_20);
    FUN_006a0280(auStack_20);
  }
  else {
    (**(code **)(*piVar4 + 0x3c))(piVar4,1,1);
    piVar4 = *(int **)(param_1 + 0x6b0);
    pcVar6 = *(code **)(*piVar4 + 0x34);
    FUN_006c173c(auStack_1c,0x42,0x7d,0xa5);
    (*pcVar6)(piVar4,1,0,auStack_1c);
    FUN_006a0280(auStack_1c);
  }
  FUN_003c9b14(*(undefined4 *)(*(int *)(param_1 + 0x6b0) + 0x28));
  uVar5 = *(undefined4 *)(param_1 + 0x128);
  uVar7 = (**(code **)(**(int **)(param_1 + 0x6b0) + 0x14))();
  FUN_007ccc24(uVar5,uVar7,0xffffffff);
  FUN_001efe14(*(undefined4 *)(param_1 + 0x6b0));
  FUN_001efe5c(*(undefined4 *)(param_1 + 0x6b0));
  FUN_002ee9a0(param_1,*(undefined4 *)(param_1 + 0x6b0));
  return;
}

