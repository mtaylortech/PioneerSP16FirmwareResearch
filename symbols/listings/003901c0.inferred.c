/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

undefined4
FUN_003901c0(undefined4 param_1,undefined4 param_2,undefined4 param_3,undefined4 param_4,
            char param_5)

{
  int iVar1;
  int local_18;
  undefined1 auStack_14 [8];
  
  iVar1 = DAT_00390258;
  if (param_5 != '\0') {
    iVar1 = DAT_00390258 + -4;
  }
  FUN_0038fef4(&local_18,param_2,param_3,iVar1);
  if (local_18 == 0) {
    FUN_006c16fc(auStack_14,0x26ffffff);
    FUN_00394264(param_1,param_4,auStack_14);
    FUN_006a0280(auStack_14);
  }
  else {
    FUN_006d32c4(param_1,&local_18);
  }
  FUN_00707778(&local_18);
  return param_1;
}

