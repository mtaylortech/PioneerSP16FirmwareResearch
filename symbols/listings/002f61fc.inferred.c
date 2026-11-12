/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_002f61fc(void)

{
  int *piVar1;
  undefined4 extraout_r2;
  undefined4 in_r3;
  
  piVar1 = (int *)FUN_0032b664();
  piVar1 = (int *)(**(code **)(*piVar1 + 0xa4))
                            (piVar1,8,extraout_r2,*(code **)(*piVar1 + 0xa4),in_r3);
  (**(code **)(*piVar1 + 0x10))();
  return;
}

