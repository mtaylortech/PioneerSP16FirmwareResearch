/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

undefined4 candidate_00391fdc(int param_1)

{
  undefined4 uVar1;
  int iVar2;
  
  if (*(int *)(param_1 + 0x94) < 1) {
    return 0;
  }
  iVar2 = **(int **)(param_1 + 0x8c);
  if (iVar2 != 0) {
    if (*(int *)(param_1 + 0x98) == iVar2) {
      return 0;
    }
    uVar1 = FUN_00391d58(param_1,iVar2,0);
    return uVar1;
  }
  return 0;
}

