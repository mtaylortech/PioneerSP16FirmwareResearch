/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_003114ac(int param_1,undefined4 param_2)

{
  int *piVar1;
  int iVar2;
  undefined4 uVar3;
  
  iVar2 = *(int *)(param_1 + 4);
  uVar3 = *(undefined4 *)(iVar2 + 0x54);
  if (*(int *)(iVar2 + 0x60) != 0) {
    return;
  }
  iVar2 = *(int *)(iVar2 + 100);
  if (iVar2 == -1) {
    return;
  }
  piVar1 = (int *)FUN_0032b664();
  piVar1 = (int *)(**(code **)(*piVar1 + 0x30))();
  (**(code **)(*piVar1 + 0x58))(piVar1,uVar3,iVar2,param_2);
  return;
}

