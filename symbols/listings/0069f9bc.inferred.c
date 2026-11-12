/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_0069f9bc(int param_1)

{
  char cVar1;
  bool bVar2;
  uint uVar3;
  int *piVar4;
  uint uVar5;
  int iVar6;
  int iVar7;
  int *piVar8;
  int *piVar9;
  
  uVar3 = FUN_00639224();
  piVar4 = operator_new(8);
  iVar6 = DAT_0069fce8;
  piVar4[1] = 0;
  piVar9 = piVar4 + 1;
  *piVar4 = iVar6;
  DataMemoryBarrier(0xf);
  do {
    bVar2 = (bool)hasExclusiveAccess(piVar9);
  } while (!bVar2);
  *piVar9 = *piVar9 + 1;
  iVar6 = DAT_0069fcec;
  DataMemoryBarrier(0xf);
  cVar1 = *(char *)(param_1 + 0xd0);
  do {
    if (cVar1 != '\0') {
      DataMemoryBarrier(0xf);
      do {
        iVar6 = *piVar9;
        bVar2 = (bool)hasExclusiveAccess(piVar9);
      } while (!bVar2);
      *piVar9 = iVar6 + -1;
      DataMemoryBarrier(0xf);
      if (iVar6 + -1 == 0) {
        (**(code **)(*piVar4 + 4))(piVar4);
        return;
      }
      return;
    }
    uVar5 = FUN_00639224();
    if (uVar5 == uVar3) {
      FUN_00644ec0(param_1,1);
    }
    else {
      if (uVar5 < uVar3) {
        uVar3 = ~uVar3;
      }
      else {
        uVar3 = -uVar3;
      }
      pthread_mutex_lock(DAT_0069fcf0);
      for (iVar7 = *(int *)(param_1 + 0xe0); iVar7 != 0; iVar7 = *(int *)(iVar7 + 0x10)) {
        *(uint *)(iVar7 + 4) = *(int *)(iVar7 + 4) - (uVar5 + uVar3);
      }
      if (*(int *)(param_1 + 0xe0) == 0) {
        iVar7 = 1000;
      }
      else {
        iVar7 = *(int *)(*(int *)(param_1 + 0xe0) + 4);
      }
      pthread_mutex_unlock(DAT_0069fcf0);
      if (iVar7 < 1) {
        piVar8 = (int *)(param_1 + 0xe4);
        DataMemoryBarrier(0xf);
        do {
          iVar7 = *piVar8;
          if (iVar7 != 0) goto LAB_0069fb2c;
          bVar2 = (bool)hasExclusiveAccess(piVar8);
        } while (!bVar2);
        *piVar8 = 1;
        iVar7 = 0;
        DataMemoryBarrier(0xf);
LAB_0069fb2c:
        if (iVar7 == 0) {
          if (((DAT_00f6e648 == 0) || (*(char *)(DAT_00f6e648 + 4) != '\0')) ||
             (iVar7 = FUN_006986a0(piVar4), iVar7 == 0)) {
            DataMemoryBarrier(0xf);
            do {
              bVar2 = (bool)hasExclusiveAccess(piVar9);
            } while (!bVar2);
            *piVar9 = *piVar9 + 1;
            DataMemoryBarrier(0xf);
            DataMemoryBarrier(0xf);
            do {
              iVar7 = *piVar9;
              bVar2 = (bool)hasExclusiveAccess(piVar9);
            } while (!bVar2);
            *piVar9 = iVar7 + -1;
            DataMemoryBarrier(0xf);
            if (iVar7 + -1 == 0) {
              (**(code **)(*piVar4 + 4))(piVar4);
            }
          }
          do {
            DataMemoryBarrier(0xf);
            do {
              iVar7 = *piVar8;
              bVar2 = (bool)hasExclusiveAccess(piVar8);
            } while (!bVar2);
            *piVar8 = iVar7;
            DataMemoryBarrier(0xf);
            if (iVar7 == 0) goto LAB_0069faa4;
            FUN_00644ec0(param_1,4);
            if (*(char *)(param_1 + 0xd0) != '\0') {
              DataMemoryBarrier(0xf);
              do {
                iVar6 = *piVar9;
                bVar2 = (bool)hasExclusiveAccess(piVar9);
              } while (!bVar2);
              *piVar9 = iVar6 + -1;
              DataMemoryBarrier(0xf);
              if (iVar6 + -1 == 0) {
                (**(code **)(*piVar4 + 4))(piVar4);
                return;
              }
              return;
            }
            uVar3 = FUN_00639224();
          } while (uVar3 <= uVar5 + 300);
          if (((*(int *)(iVar6 + 4) == 0) || (*(char *)(*(int *)(iVar6 + 4) + 4) != '\0')) ||
             (iVar7 = FUN_006986a0(piVar4), iVar7 == 0)) {
            DataMemoryBarrier(0xf);
            do {
              bVar2 = (bool)hasExclusiveAccess(piVar9);
            } while (!bVar2);
            *piVar9 = *piVar9 + 1;
            DataMemoryBarrier(0xf);
            DataMemoryBarrier(0xf);
            do {
              iVar7 = *piVar9;
              bVar2 = (bool)hasExclusiveAccess(piVar9);
            } while (!bVar2);
            *piVar9 = iVar7 + -1;
            DataMemoryBarrier(0xf);
            if (iVar7 + -1 == 0) {
              (**(code **)(*piVar4 + 4))(piVar4);
            }
          }
        }
      }
      else {
        if (0x31 < iVar7) {
          iVar7 = 0x32;
        }
        FUN_00644ec0(param_1,iVar7);
      }
    }
LAB_0069faa4:
    cVar1 = *(char *)(param_1 + 0xd0);
    uVar3 = uVar5;
  } while( true );
}

