/* INFERRED PSEUDOCODE; names/types/indirect targets need instruction checks. No target execution. */

undefined4 FUN_006987f8(int *param_1)

{
  bool bVar1;
  int *piVar2;
  int iVar3;
  
  if ((*(int *)(DAT_006988b4 + 4) == 0) || (*(char *)(*(int *)(DAT_006988b4 + 4) + 4) != '\0')) {
    if (param_1 == (int *)0x0) {
      return 0;
    }
  }
  else {
    iVar3 = FUN_006986a0();
    if (iVar3 != 0) {
      return 1;
    }
    if (param_1 == (int *)0x0) {
      return 0;
    }
  }
  piVar2 = param_1 + 1;
  DataMemoryBarrier(0xf);
  do {
    bVar1 = (bool)hasExclusiveAccess(piVar2);
  } while (!bVar1);
  *piVar2 = *piVar2 + 1;
  DataMemoryBarrier(0xf);
  DataMemoryBarrier(0xf);
  do {
    iVar3 = *piVar2;
    bVar1 = (bool)hasExclusiveAccess(piVar2);
  } while (!bVar1);
  *piVar2 = iVar3 + -1;
  DataMemoryBarrier(0xf);
  if (iVar3 + -1 != 0) {
    return 0;
  }
  (**(code **)(*param_1 + 4))(param_1);
  return 0;
}

