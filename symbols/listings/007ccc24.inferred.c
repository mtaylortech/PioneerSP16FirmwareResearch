/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_007ccc24(undefined4 param_1,int *param_2,undefined4 param_3)

{
  if (param_2 == (int *)0x0) {
    return;
  }
  (**(code **)(*param_2 + 0x2c))(param_2,1);
  FUN_007cbd94(param_1,param_2,param_3);
  return;
}

