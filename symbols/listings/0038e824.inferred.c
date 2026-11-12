/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_0038e824(int param_1,uint param_2)

{
  int iVar1;
  
  if (*(byte *)(param_1 + 200) == param_2) {
    return;
  }
  *(char *)(param_1 + 200) = (char)param_2;
  iVar1 = FUN_0078e78c();
  if (iVar1 == 0) {
    return;
  }
  FUN_00790630(param_1);
  return;
}

