/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_00392940(int param_1,undefined4 param_2)

{
  int iVar1;
  int local_30;
  int local_2c;
  int local_28;
  int local_24;
  int local_20;
  int local_1c;
  undefined4 local_18;
  undefined4 uStack_14;
  
  iVar1 = FUN_00761e8c();
  if ((iVar1 != 0) && (*(char *)(param_1 + 0x101) != '\0')) {
    *(undefined1 *)(param_1 + 0x101) = 0;
    FUN_0076165c(&local_30,param_1);
    FUN_007649e0(&local_20,param_2);
    if (local_30 <= local_20) {
      if (((local_2c <= local_1c) && (local_20 < local_30 + local_28)) &&
         (local_1c < local_2c + local_24)) {
        local_18 = *DAT_00392a0c;
        uStack_14 = DAT_00392a0c[1];
        FUN_00394614(param_1 + 0x7c,local_18,uStack_14,param_1 + 0x74);
      }
    }
    iVar1 = FUN_0078e78c(param_1);
    if (iVar1 != 0) {
      FUN_00790630(param_1);
    }
  }
  return;
}

