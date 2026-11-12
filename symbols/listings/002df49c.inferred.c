/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_002df49c(int param_1,int param_2)

{
  int iVar1;
  int iVar2;
  int iVar3;
  undefined1 local_11;
  
  iVar3 = param_1 + 0x20;
  local_11 = 0;
  iVar1 = FUN_002f3b40(iVar3);
  if (iVar1 != 2) {
    iVar1 = FUN_002f3d94(iVar3,&local_11);
    iVar2 = *(int *)(param_1 + 0x48);
    if (iVar2 <= iVar1 + param_2) {
      iVar1 = FUN_002f3d94(iVar3,&local_11);
      iVar2 = *(int *)(param_1 + 0x4c);
      if (param_2 + iVar1 <= iVar2) {
        iVar2 = FUN_002f3d94(iVar3,&local_11);
        iVar2 = param_2 + iVar2;
      }
    }
    FUN_002f3ff4(iVar3,iVar2);
  }
  return;
}

