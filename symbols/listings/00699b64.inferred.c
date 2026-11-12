/* INFERRED PSEUDOCODE; names/types/indirect targets need instruction checks. No target execution. */

void FUN_00699b64(int param_1)

{
  bool bVar1;
  int iVar2;
  int iVar3;
  int *piVar4;
  int *piVar5;
  
  piVar4 = (int *)(*(int *)(param_1 + 4) + 8);
  DataMemoryBarrier(0xf);
  do {
    iVar2 = *piVar4;
    if (iVar2 != 0) goto LAB_00699ba0;
    bVar1 = (bool)hasExclusiveAccess(piVar4);
  } while (!bVar1);
  *piVar4 = 1;
  iVar2 = 0;
  DataMemoryBarrier(0xf);
LAB_00699ba0:
  if (iVar2 != 0) {
    return;
  }
  piVar4 = *(int **)(param_1 + 4);
  if (((*(int *)(DAT_00699c88 + 4) != 0) && (*(char *)(*(int *)(DAT_00699c88 + 4) + 4) == '\0')) &&
     (iVar2 = FUN_006986a0(piVar4), iVar2 != 0)) {
    return;
  }
  if (piVar4 != (int *)0x0) {
    piVar5 = piVar4 + 1;
    DataMemoryBarrier(0xf);
    do {
      bVar1 = (bool)hasExclusiveAccess(piVar5);
    } while (!bVar1);
    *piVar5 = *piVar5 + 1;
    DataMemoryBarrier(0xf);
    DataMemoryBarrier(0xf);
    do {
      iVar2 = *piVar5;
      bVar1 = (bool)hasExclusiveAccess(piVar5);
    } while (!bVar1);
    *piVar5 = iVar2 + -1;
    DataMemoryBarrier(0xf);
    if (iVar2 + -1 == 0) {
      (**(code **)(*piVar4 + 4))(piVar4);
    }
  }
  piVar4 = (int *)(*(int *)(param_1 + 4) + 8);
  iVar2 = *(int *)(*(int *)(param_1 + 4) + 8);
  do {
    DataMemoryBarrier(0xf);
    do {
      iVar3 = *piVar4;
      if (*piVar4 != iVar2) goto LAB_00699c68;
      bVar1 = (bool)hasExclusiveAccess(piVar4);
    } while (!bVar1);
    *piVar4 = 0;
    DataMemoryBarrier(0xf);
    iVar3 = iVar2;
LAB_00699c68:
    if (iVar3 == iVar2) {
      return;
    }
    iVar2 = *piVar4;
  } while( true );
}

