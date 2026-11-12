/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

bool FUN_002fdf7c(void)

{
  int *piVar1;
  int iVar2;
  
  piVar1 = (int *)FUN_0032b664();
  iVar2 = (**(code **)(*piVar1 + 0x90))();
  return iVar2 != 0;
}

