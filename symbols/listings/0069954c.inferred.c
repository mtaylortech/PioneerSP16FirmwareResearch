/* INFERRED PSEUDOCODE; names/types/indirect targets need instruction checks. No target execution. */

void FUN_0069954c(int param_1,int *param_2)

{
  bool bVar1;
  int *piVar2;
  int iVar3;
  int *piVar4;
  
  if (param_1 == 0) {
    piVar4 = (int *)0x0;
  }
  else {
    piVar4 = *(int **)(param_1 + 4);
    if (piVar4 == (int *)0x0) {
      piVar4 = operator_new(0xc);
      piVar2 = *(int **)(param_1 + 4);
      piVar4[1] = 0;
      iVar3 = DAT_00699724;
      piVar4[2] = param_1;
      *piVar4 = iVar3;
      if (piVar4 != piVar2) {
        piVar2 = piVar4 + 1;
        DataMemoryBarrier(0xf);
        do {
          bVar1 = (bool)hasExclusiveAccess(piVar2);
        } while (!bVar1);
        *piVar2 = *piVar2 + 1;
        DataMemoryBarrier(0xf);
        piVar2 = *(int **)(param_1 + 4);
        *(int **)(param_1 + 4) = piVar4;
        if (piVar2 != (int *)0x0) {
          piVar4 = piVar2 + 1;
          DataMemoryBarrier(0xf);
          do {
            iVar3 = *piVar4;
            bVar1 = (bool)hasExclusiveAccess(piVar4);
          } while (!bVar1);
          *piVar4 = iVar3 + -1;
          DataMemoryBarrier(0xf);
          if (iVar3 + -1 == 0) {
            (**(code **)(*piVar2 + 4))();
          }
          piVar4 = *(int **)(param_1 + 4);
        }
      }
    }
  }
  piVar2 = (int *)param_2[2];
  if (piVar2 != piVar4) {
    if (piVar4 != (int *)0x0) {
      piVar2 = piVar4 + 1;
      DataMemoryBarrier(0xf);
      do {
        bVar1 = (bool)hasExclusiveAccess(piVar2);
      } while (!bVar1);
      *piVar2 = *piVar2 + 1;
      DataMemoryBarrier(0xf);
      piVar2 = (int *)param_2[2];
    }
    param_2[2] = (int)piVar4;
    if (piVar2 != (int *)0x0) {
      piVar4 = piVar2 + 1;
      DataMemoryBarrier(0xf);
      do {
        iVar3 = *piVar4;
        bVar1 = (bool)hasExclusiveAccess(piVar4);
      } while (!bVar1);
      *piVar4 = iVar3 + -1;
      DataMemoryBarrier(0xf);
      if (iVar3 + -1 == 0) {
        (**(code **)(*piVar2 + 4))();
      }
    }
  }
  if (((*(int *)(DAT_00699720 + 4) != 0) && (*(char *)(*(int *)(DAT_00699720 + 4) + 4) == '\0')) &&
     (iVar3 = FUN_006986a0(param_2), iVar3 != 0)) {
    return;
  }
  piVar4 = param_2 + 1;
  DataMemoryBarrier(0xf);
  do {
    bVar1 = (bool)hasExclusiveAccess(piVar4);
  } while (!bVar1);
  *piVar4 = *piVar4 + 1;
  DataMemoryBarrier(0xf);
  DataMemoryBarrier(0xf);
  do {
    iVar3 = *piVar4;
    bVar1 = (bool)hasExclusiveAccess(piVar4);
  } while (!bVar1);
  *piVar4 = iVar3 + -1;
  DataMemoryBarrier(0xf);
  if (iVar3 + -1 != 0) {
    return;
  }
  (**(code **)(*param_2 + 4))(param_2);
  return;
}

