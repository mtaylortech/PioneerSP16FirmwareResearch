/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_002df3b4(int param_1,int param_2)

{
  int iVar1;
  int iVar2;
  int iVar3;
  
  iVar3 = param_1 + 0x20;
  iVar1 = FUN_002f61fc(iVar3);
  iVar2 = *(int *)(param_1 + 0x9c);
  if (iVar2 <= iVar1 + param_2) {
    iVar1 = FUN_002f61fc(iVar3);
    iVar2 = *(int *)(param_1 + 0xa0);
    if (param_2 + iVar1 <= iVar2) {
      iVar2 = FUN_002f61fc(iVar3);
      iVar2 = param_2 + iVar2;
    }
  }
  FUN_002f6224(iVar3,iVar2);
  return;
}

