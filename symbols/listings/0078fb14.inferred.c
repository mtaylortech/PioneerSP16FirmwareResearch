/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_0078fb14(int param_1,uint *param_2)

{
  uint uVar1;
  int *piVar2;
  uint uVar3;
  int iVar4;
  int iVar5;
  uint uVar6;
  uint uVar7;
  undefined8 local_20;
  undefined8 local_18;
  
  uVar7 = *param_2;
  uVar1 = param_2[1];
  uVar6 = uVar7 & ~((int)uVar7 >> 0x1f);
  uVar3 = uVar1 & ~((int)uVar1 >> 0x1f);
  if ((int)(uVar7 + param_2[2]) < *(int *)(param_1 + 0x18)) {
    iVar4 = (uVar7 + param_2[2]) - uVar6;
  }
  else {
    iVar4 = *(int *)(param_1 + 0x18) - uVar6;
  }
  if ((int)(uVar1 + param_2[3]) < *(int *)(param_1 + 0x1c)) {
    iVar5 = (uVar1 + param_2[3]) - uVar3;
  }
  else {
    iVar5 = *(int *)(param_1 + 0x1c) - uVar3;
  }
  if (-1 < iVar5 && -1 < iVar4) {
    local_20 = CONCAT44(uVar3,uVar6);
    local_18 = CONCAT44(iVar5,iVar4);
    if ((((iVar4 != 0) && (iVar5 != 0)) && ((*(byte *)(param_1 + 0x68) & 2) != 0)) &&
       ((piVar2 = *(int **)(param_1 + 0x40), piVar2 == (int *)0x0 ||
        (iVar4 = (**(code **)(*piVar2 + 0x10))(piVar2,&local_20), iVar4 != 0)))) {
      FUN_0078f8d8(param_1,&local_20);
    }
  }
  return;
}

