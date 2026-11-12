/* INFERRED PSEUDOCODE; names/types/indirect targets need instruction checks. No target execution. */

int * FUN_00696d58(int *param_1)

{
  bool bVar1;
  int *piVar2;
  int iVar3;
  int *piVar4;
  int iVar5;
  
  if (*param_1 != 0) {
    iVar5 = *(int *)(DAT_00696e2c + 4);
    FUN_00645778(*param_1 + 0x58);
    piVar2 = (int *)*param_1;
    if (piVar2 != (int *)0x0) {
      piVar4 = piVar2 + 1;
      *param_1 = 0;
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
    if (iVar5 != 0) {
      *(undefined4 *)(iVar5 + 0xc) = 0;
      pthread_mutex_unlock((pthread_mutex_t *)(iVar5 + 0x10));
    }
    piVar2 = (int *)*param_1;
    if (piVar2 != (int *)0x0) {
      piVar4 = piVar2 + 1;
      DataMemoryBarrier(0xf);
      do {
        iVar5 = *piVar4;
        bVar1 = (bool)hasExclusiveAccess(piVar4);
      } while (!bVar1);
      *piVar4 = iVar5 + -1;
      DataMemoryBarrier(0xf);
      if (iVar5 + -1 == 0) {
        (**(code **)(*piVar2 + 4))();
      }
    }
  }
  return param_1;
}

