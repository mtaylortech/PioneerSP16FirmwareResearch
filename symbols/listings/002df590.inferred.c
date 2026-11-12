/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_002df590(int param_1,int param_2)

{
  int iVar1;
  int iVar2;
  int iVar3;
  undefined1 local_11;
  
  iVar3 = param_1 + 0x20;
  local_11 = 0;
  iVar1 = FUN_002f3b40(iVar3);
  if ((iVar1 != 2) && (iVar1 = FUN_002fdf7c(iVar3), iVar1 != 0)) {
    iVar1 = FUN_002f5e7c(iVar3,&local_11);
    iVar2 = *(int *)(param_1 + 0x80);
    if (iVar2 <= iVar1 + param_2) {
      iVar1 = FUN_002f5e7c(iVar3,&local_11);
      iVar2 = *(int *)(param_1 + 0x84);
      if (param_2 + iVar1 <= iVar2) {
        iVar2 = FUN_002f5e7c(iVar3,&local_11);
        iVar2 = param_2 + iVar2;
      }
    }
    FUN_002f60dc(iVar3,iVar2);
  }
  return;
}

