/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_00392a10(int param_1)

{
  undefined4 *puVar1;
  int iVar2;
  
  iVar2 = FUN_00761e8c();
  puVar1 = DAT_00392a80;
  if ((iVar2 != 0) && (*(char *)(param_1 + 0x101) != '\x01')) {
    *(undefined1 *)(param_1 + 0x101) = 1;
    FUN_00394614(param_1 + 0x7c,*puVar1,puVar1[1],param_1 + 0x74);
    iVar2 = FUN_0078e78c(param_1);
    if (iVar2 != 0) {
      FUN_00790630(param_1);
      return;
    }
  }
  return;
}

