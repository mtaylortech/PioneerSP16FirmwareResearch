/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

int FUN_00523514(int param_1)

{
  int iVar1;
  undefined4 uVar2;
  undefined1 auStack_28 [16];
  undefined1 auStack_18 [8];
  
  iVar1 = FUN_00517cf0(*(undefined4 *)(param_1 + 0x1c0));
  if (iVar1 != -1) {
    FUN_0052a18c(param_1 + 8);
    FUN_00529928();
    uVar2 = FUN_00528c74();
    FUN_00526dc4(auStack_28,0,uVar2);
    FUN_005224c4(*(undefined4 *)(param_1 + 0x1c4),auStack_28);
    iVar1 = FUN_00517cc0(*(undefined4 *)(param_1 + 0x1c0));
    if (iVar1 == -1) {
      FUN_00527080(auStack_28);
      iVar1 = -1;
    }
    else {
      if (*(char *)(*(int *)(param_1 + 0x1c4) + 8) != '\0') {
        FUN_0052a0d4(param_1 + 8,DAT_005235dc);
      }
      FUN_00527080(auStack_28);
      FUN_0052323c(param_1,auStack_18);
      FUN_005114b4(*(undefined4 *)(param_1 + 0x1d4),auStack_18);
      iVar1 = 0;
    }
  }
  return iVar1;
}

