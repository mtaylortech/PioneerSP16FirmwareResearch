/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_0028f820(int *param_1,undefined4 param_2,undefined4 param_3,undefined4 param_4)

{
  int iVar1;
  int *piVar2;
  undefined4 uVar3;
  code *pcVar4;
  int iVar5;
  int aiStack_18 [2];
  undefined4 uStack_10;
  
  uStack_10 = param_4;
  iVar1 = FUN_002fa970(param_1 + 8);
  if (iVar1 != 0) {
    return;
  }
  if (*(char *)(DAT_0028f87c + 2) != '\0') {
    param_1[0x52] = 2;
    iVar5 = param_1[0x51];
    iVar1 = FUN_002ee9fc();
    if (iVar5 == iVar1) {
      return;
    }
    FUN_0028f78c(param_1,1);
    return;
  }
  piVar2 = (int *)(**(code **)(*param_1 + 0x30))();
  FUN_00627ba0(aiStack_18,DAT_002eb56c);
  iVar1 = *piVar2;
  FUN_006280c8(aiStack_18);
  if (iVar1 != aiStack_18[0]) {
    piVar2 = (int *)param_1[4];
    pcVar4 = *(code **)(*piVar2 + 8);
    uVar3 = (**(code **)(*param_1 + 0x30))(param_1);
    (*pcVar4)(piVar2,uVar3);
  }
  return;
}

