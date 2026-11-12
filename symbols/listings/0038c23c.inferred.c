/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_0038c23c(int param_1,int param_2,undefined4 param_3,undefined4 param_4)

{
  int *piVar1;
  uint uVar2;
  int iVar3;
  
  if ((*(uint *)(param_2 + 0x10) & 0x20) == 0) {
    return;
  }
  piVar1 = *(int **)(param_1 + 0x78);
  if (piVar1 == (int *)0x0) {
    return;
  }
  if (((uint)piVar1 & 3) != 0) {
    return;
  }
  iVar3 = *piVar1;
  uVar2 = (int)piVar1 + *(int *)(iVar3 + -0xc);
  if (uVar2 == 0) {
    return;
  }
  if ((uVar2 & 3) != 0) {
    return;
  }
  if (*(int *)((int)piVar1 + *(int *)(iVar3 + -0xc)) != 0x5e715e28) {
    return;
  }
  (**(code **)(iVar3 + 200))(piVar1,1,iVar3,*(code **)(iVar3 + 200),param_4);
  return;
}

