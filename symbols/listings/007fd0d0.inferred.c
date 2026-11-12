/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_007fd0d0(int param_1,uint *param_2)

{
  uint uVar1;
  uint uVar2;
  int iVar3;
  uint uVar4;
  int iVar5;
  int iVar6;
  int iVar7;
  uint uVar8;
  undefined8 local_20;
  undefined8 local_18;
  
  uVar2 = *param_2;
  uVar4 = param_2[1];
  uVar8 = uVar2 & ~((int)uVar2 >> 0x1f);
  uVar1 = uVar4 & ~((int)uVar4 >> 0x1f);
  if ((int)(uVar2 + param_2[2]) < *(int *)(param_1 + 0x48)) {
    iVar3 = (uVar2 + param_2[2]) - uVar8;
  }
  else {
    iVar3 = *(int *)(param_1 + 0x48) - uVar8;
  }
  if ((int)(uVar4 + param_2[3]) < *(int *)(param_1 + 0x4c)) {
    iVar5 = (uVar4 + param_2[3]) - uVar1;
  }
  else {
    iVar5 = *(int *)(param_1 + 0x4c) - uVar1;
  }
  iVar7 = *(int *)(param_1 + 0x34);
  if (iVar5 < 0 || iVar3 < 0) {
    iVar6 = *(int *)(iVar7 + 8);
    local_20 = 0;
    local_18 = 0;
  }
  else {
    local_20 = CONCAT44(uVar1,uVar8);
    iVar6 = *(int *)(iVar7 + 8);
    local_18 = CONCAT44(iVar5,iVar3);
  }
  if (iVar6 < 1) {
    FUN_0069bf5c(iVar7,10);
  }
  FUN_004ffc80(iVar7 + 0x20,&local_20);
  return;
}

