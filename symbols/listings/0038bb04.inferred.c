/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_0038bb04(int param_1)

{
  int iVar1;
  int iVar2;
  int iVar3;
  undefined1 auStack_1c [4];
  undefined1 auStack_18 [4];
  undefined1 auStack_14 [4];
  
  iVar3 = *(int *)(param_1 + 0x18);
  iVar2 = *(int *)(param_1 + 0x1c);
  iVar1 = iVar3;
  if (0 < iVar3) {
    iVar1 = iVar2;
  }
  if (0 < iVar1) {
    if (*(int *)(param_1 + 200) != 0) {
      FUN_00500b18(auStack_1c,param_1 + 0xb8,iVar3,iVar2);
      FUN_00707778(auStack_1c);
    }
    if (*(int *)(param_1 + 0xa4) != 0) {
      FUN_00500b18(auStack_18,param_1 + 0x94,iVar3,iVar2);
      FUN_00707778(auStack_18);
    }
    if (*(int *)(param_1 + 0xec) != 0) {
      FUN_00500b18(auStack_14,param_1 + 0xdc,iVar3,iVar2);
      FUN_00707778(auStack_14);
    }
  }
  return;
}

