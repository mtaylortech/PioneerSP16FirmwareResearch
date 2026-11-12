/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

int FUN_002f35b0(undefined4 param_1,int param_2)

{
  int *piVar1;
  int iVar2;
  
  piVar1 = (int *)FUN_0032b664();
  piVar1 = (int *)(**(code **)(*piVar1 + 0x10))(piVar1,param_2);
  if ((piVar1 != (int *)0x0) && (((uint)piVar1 & 3) == 0)) {
    iVar2 = (**(code **)(*piVar1 + 0x54))();
    if (iVar2 < 0) {
      iVar2 = param_2;
    }
    return iVar2;
  }
  FUN_004f782c(DAT_002f360c,DAT_002f3610,DAT_002f3614);
  return -1;
}

