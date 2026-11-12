/* INFERRED PSEUDOCODE; names/types/indirect targets need instruction checks. No target execution. */

undefined4 FUN_00699c8c(int *param_1,int param_2,int param_3)

{
  bool bVar1;
  pthread_t pVar2;
  int iVar3;
  int *piVar4;
  int *piVar5;
  int iVar6;
  int iVar7;
  int iVar8;
  
  iVar6 = DAT_0069a09c;
  iVar8 = *(int *)(DAT_0069a09c + 4);
  if (iVar8 == 0) {
    return 0;
  }
  pVar2 = pthread_self();
  if ((pVar2 == *(pthread_t *)(iVar8 + 8)) || (pVar2 == *(pthread_t *)(iVar8 + 0xc))) {
    return 1;
  }
  if (param_3 == 0 && param_2 == 0) {
    pthread_mutex_lock((pthread_mutex_t *)(iVar8 + 0x10));
  }
  else {
    iVar7 = iVar8 + 0x10;
    if (param_3 == 0) {
      if (param_2 == 0) {
        iVar3 = FUN_00644d0c(iVar7);
        while (iVar3 == 0) {
          sched_yield();
          iVar3 = FUN_00644d0c(iVar7);
        }
      }
      else {
        iVar3 = FUN_00644d0c(iVar7);
        if (iVar3 == 0) {
          if (*(char *)(param_2 + 0xd0) != '\0') {
            return 0;
          }
          while( true ) {
            sched_yield();
            iVar3 = FUN_00644d0c(iVar7);
            if (iVar3 != 0) break;
            if (*(char *)(param_2 + 0xd0) != '\0') {
              return 0;
            }
          }
        }
      }
    }
    else if (param_2 == 0) {
      while (iVar3 = FUN_00644d0c(iVar7), iVar3 == 0) {
        if (*(char *)(param_3 + 0xc) != '\0') {
          return 0;
        }
        sched_yield();
      }
    }
    else {
      iVar3 = FUN_00644d0c(iVar7);
      while (iVar3 == 0) {
        if (*(char *)(param_2 + 0xd0) != '\0') {
          return 0;
        }
        if (*(char *)(param_3 + 0xc) != '\0') {
          return 0;
        }
        sched_yield();
        iVar3 = FUN_00644d0c(iVar7);
      }
    }
  }
  piVar4 = operator_new(0xa8);
  iVar7 = DAT_0069a0a0;
  piVar4[1] = 0;
  *piVar4 = iVar7;
  FUN_00644d24(piVar4 + 2,0);
  FUN_00644d24(piVar4 + 0x16,0);
  if (piVar4 != (int *)*param_1) {
    piVar5 = piVar4 + 1;
    DataMemoryBarrier(0xf);
    do {
      bVar1 = (bool)hasExclusiveAccess(piVar5);
    } while (!bVar1);
    *piVar5 = *piVar5 + 1;
    DataMemoryBarrier(0xf);
    piVar5 = (int *)*param_1;
    *param_1 = (int)piVar4;
    if (piVar5 != (int *)0x0) {
      piVar4 = piVar5 + 1;
      DataMemoryBarrier(0xf);
      do {
        iVar7 = *piVar4;
        bVar1 = (bool)hasExclusiveAccess(piVar4);
      } while (!bVar1);
      *piVar4 = iVar7 + -1;
      DataMemoryBarrier(0xf);
      if (iVar7 + -1 == 0) {
        (**(code **)(*piVar5 + 4))();
      }
      piVar4 = (int *)*param_1;
    }
  }
  if (((*(int *)(iVar6 + 4) == 0) || (*(char *)(*(int *)(iVar6 + 4) + 4) != '\0')) ||
     (iVar6 = FUN_006986a0(piVar4), iVar6 == 0)) {
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
        iVar6 = *piVar5;
        bVar1 = (bool)hasExclusiveAccess(piVar5);
      } while (!bVar1);
      *piVar5 = iVar6 + -1;
      DataMemoryBarrier(0xf);
      if (iVar6 + -1 == 0) {
        (**(code **)(*piVar4 + 4))(piVar4);
      }
    }
    piVar4 = (int *)*param_1;
    if (piVar4 == (int *)0x0) {
      return 0;
    }
    piVar5 = piVar4 + 1;
    *param_1 = 0;
    DataMemoryBarrier(0xf);
    do {
      iVar6 = *piVar5;
      bVar1 = (bool)hasExclusiveAccess(piVar5);
    } while (!bVar1);
    *piVar5 = iVar6 + -1;
    DataMemoryBarrier(0xf);
    if (iVar6 + -1 != 0) {
      return 0;
    }
    (**(code **)(*piVar4 + 4))();
    return 0;
  }
  if (param_3 == 0) {
    if (param_2 == 0) {
      do {
        iVar6 = FUN_00644d8c(*param_1 + 8,0x14);
      } while (iVar6 == 0);
LAB_0069a058:
      pVar2 = pthread_self();
      *(pthread_t *)(iVar8 + 0xc) = pVar2;
      return 1;
    }
    do {
      iVar6 = FUN_00644d8c(*param_1 + 8,0x14);
      if (iVar6 != 0) goto LAB_0069a058;
    } while (*(char *)(param_2 + 0xd0) == '\0');
  }
  else if (param_2 == 0) {
    do {
      iVar6 = FUN_00644d8c(*param_1 + 8,0x14);
      if (iVar6 != 0) goto LAB_0069a058;
    } while (*(char *)(param_3 + 0xc) == '\0');
  }
  else {
    do {
      iVar6 = FUN_00644d8c(*param_1 + 8,0x14);
      if (iVar6 != 0) goto LAB_0069a058;
    } while ((*(char *)(param_2 + 0xd0) == '\0') && (*(char *)(param_3 + 0xc) == '\0'));
  }
  FUN_00645778(*param_1 + 0x58);
  piVar4 = (int *)*param_1;
  if (piVar4 != (int *)0x0) {
    piVar5 = piVar4 + 1;
    *param_1 = 0;
    DataMemoryBarrier(0xf);
    do {
      iVar6 = *piVar5;
      bVar1 = (bool)hasExclusiveAccess(piVar5);
    } while (!bVar1);
    *piVar5 = iVar6 + -1;
    DataMemoryBarrier(0xf);
    if (iVar6 + -1 == 0) {
      (**(code **)(*piVar4 + 4))();
    }
  }
  pthread_mutex_unlock((pthread_mutex_t *)(iVar8 + 0x10));
  return 0;
}

