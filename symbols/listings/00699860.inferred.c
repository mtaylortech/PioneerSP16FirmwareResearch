/* INFERRED PSEUDOCODE; names/types/indirect targets need instruction checks. No target execution. */

int FUN_00699860(int param_1,code *param_2,int param_3)

{
  bool bVar1;
  pthread_t pVar2;
  int *piVar3;
  int iVar4;
  int iVar5;
  int *piVar6;
  
  pVar2 = pthread_self();
  if (*(pthread_t *)(param_1 + 8) != pVar2) {
    piVar3 = operator_new(0x68);
    iVar4 = DAT_00699a0c;
    piVar3[1] = 0;
    piVar6 = piVar3 + 1;
    *piVar3 = iVar4;
    FUN_00644d24(piVar3 + 2,0);
    piVar3[0x16] = 0;
    piVar3[0x17] = (int)param_2;
    piVar3[0x18] = param_3;
    DataMemoryBarrier(0xf);
    do {
      bVar1 = (bool)hasExclusiveAccess(piVar6);
    } while (!bVar1);
    *piVar6 = *piVar6 + 1;
    DataMemoryBarrier(0xf);
    if (((*(int *)(DAT_00699a10 + 4) == 0) || (*(char *)(*(int *)(DAT_00699a10 + 4) + 4) != '\0'))
       || (iVar4 = FUN_006986a0(piVar3), iVar4 == 0)) {
      DataMemoryBarrier(0xf);
      do {
        bVar1 = (bool)hasExclusiveAccess(piVar6);
      } while (!bVar1);
      *piVar6 = *piVar6 + 1;
      DataMemoryBarrier(0xf);
      DataMemoryBarrier(0xf);
      do {
        iVar4 = *piVar6;
        bVar1 = (bool)hasExclusiveAccess(piVar6);
      } while (!bVar1);
      *piVar6 = iVar4 + -1;
      DataMemoryBarrier(0xf);
      if (iVar4 + -1 == 0) {
        (**(code **)(*piVar3 + 4))(piVar3);
      }
      iVar4 = 0;
    }
    else {
      FUN_00644d8c(piVar3 + 2,0xffffffff);
      iVar4 = piVar3[0x16];
    }
    DataMemoryBarrier(0xf);
    do {
      iVar5 = *piVar6;
      bVar1 = (bool)hasExclusiveAccess(piVar6);
    } while (!bVar1);
    *piVar6 = iVar5 + -1;
    DataMemoryBarrier(0xf);
    if (iVar5 + -1 == 0) {
      (**(code **)(*piVar3 + 4))(piVar3);
    }
    return iVar4;
  }
  iVar4 = (*param_2)(param_3);
  return iVar4;
}

