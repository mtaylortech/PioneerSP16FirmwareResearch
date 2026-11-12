/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_004c8c90(int param_1)

{
  int iVar1;
  int iVar2;
  undefined4 uVar3;
  undefined1 auStack_14 [8];
  
  iVar2 = param_1 + 0xcc;
  iVar1 = FUN_00646364(iVar2);
  if (iVar1 != 0) {
    uVar3 = *(undefined4 *)(param_1 + 0xd4);
    FUN_0070974c(auStack_14,iVar2);
    FUN_0038e768(uVar3,auStack_14,DAT_004c8cf8);
    FUN_00707778(auStack_14);
  }
  FUN_00658f1c(iVar2,DAT_004c8cfc);
  return;
}

