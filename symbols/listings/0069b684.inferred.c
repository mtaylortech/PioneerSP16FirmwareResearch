/* INFERRED PSEUDOCODE; names/types/indirect targets need instruction checks. No target execution. */

undefined4 FUN_0069b684(int param_1)

{
  char cVar1;
  bool bVar2;
  timeval tVar3;
  int iVar4;
  void *pvVar5;
  int iVar6;
  undefined4 uVar7;
  int iVar8;
  uint uVar9;
  int *piVar10;
  pthread_mutex_t *__mutex;
  int iVar11;
  int *piVar12;
  undefined4 *puVar13;
  fd_set local_180;
  int local_100 [4];
  int local_f0;
  int local_a0 [4];
  int local_90;
  timeval local_40;
  undefined1 uStack_31;
  
  iVar8 = DAT_0069b940;
  tVar3 = DAT_0069b938;
LAB_0069b6a4:
  cVar1 = *(char *)(iVar8 + 0x60);
  do {
    if (cVar1 != '\0') {
      return 0;
    }
    if (*(char *)(iVar8 + 8) != '\0') {
      piVar12 = (int *)(DAT_0069b940 + 0x3c);
      *(undefined1 *)(DAT_0069b940 + 0x60) = 1;
      if (*piVar12 != 0) {
        FUN_0064582c();
        return 0;
      }
      return 0;
    }
    __mutex = *(pthread_mutex_t **)(iVar8 + 0x50);
    uVar9 = __mutex[2].__data.__lock + 1;
    __mutex[2].__data.__lock = uVar9;
    if ((uVar9 & 1) == 0) {
      pthread_mutex_lock(__mutex);
      if (0 < *(int *)((int)__mutex + 0x2c)) {
        *(int *)((int)__mutex + 0x2c) = *(int *)((int)__mutex + 0x2c) + -1;
        pthread_mutex_unlock(__mutex);
        read(*(int *)((int)__mutex + 0x28),&uStack_31,1);
        pthread_mutex_lock(__mutex);
      }
      iVar4 = *(int *)((int)__mutex + 0x20);
      if (iVar4 == 0) {
        pthread_mutex_unlock(__mutex);
      }
      else {
        puVar13 = *(undefined4 **)(__mutex + 1);
        piVar12 = (int *)*puVar13;
        if (piVar12 != (int *)0x0) {
          piVar10 = piVar12 + 1;
          DataMemoryBarrier(0xf);
          do {
            bVar2 = (bool)hasExclusiveAccess(piVar10);
          } while (!bVar2);
          *piVar10 = *piVar10 + 1;
          DataMemoryBarrier(0xf);
          DataMemoryBarrier(0xf);
          do {
            iVar4 = *piVar10;
            bVar2 = (bool)hasExclusiveAccess(piVar10);
          } while (!bVar2);
          *piVar10 = iVar4 + -1;
          DataMemoryBarrier(0xf);
          if (iVar4 + -1 == 0) {
            (**(code **)(*piVar12 + 4))(piVar12);
          }
          iVar4 = *(int *)((int)__mutex + 0x20);
        }
        iVar4 = iVar4 + -1;
        *(int *)((int)__mutex + 0x20) = iVar4;
        if (0 < iVar4) {
          memmove(puVar13,puVar13 + 1,iVar4 * 4);
          iVar4 = *(int *)((int)__mutex + 0x20);
        }
        if ((iVar4 * 2 < *(int *)((int)__mutex + 0x1c)) && (iVar4 < *(int *)((int)__mutex + 0x1c)))
        {
          pvVar5 = (void *)__mutex[1].__data.__lock;
          if (iVar4 < 1) {
            free(pvVar5);
            *(int *)((int)__mutex + 0x1c) = iVar4;
            __mutex[1].__data.__lock = 0;
          }
          else {
            if (pvVar5 == (void *)0x0) {
              pvVar5 = malloc(iVar4 << 2);
              __mutex[1].__data.__lock = (int)pvVar5;
            }
            else {
              pvVar5 = realloc(pvVar5,iVar4 << 2);
              __mutex[1].__data.__lock = (int)pvVar5;
            }
            *(int *)((int)__mutex + 0x1c) = iVar4;
          }
        }
        pthread_mutex_unlock(__mutex);
        if (piVar12 != (int *)0x0) {
          (**(code **)(*piVar12 + 8))(piVar12);
          piVar10 = piVar12 + 1;
          DataMemoryBarrier(0xf);
          do {
            iVar8 = *piVar10;
            bVar2 = (bool)hasExclusiveAccess(piVar10);
          } while (!bVar2);
          *piVar10 = iVar8 + -1;
          DataMemoryBarrier(0xf);
          if (iVar8 + -1 != 0) {
            return 1;
          }
          (**(code **)(*piVar12 + 4))(piVar12);
          return 1;
        }
      }
      if (*(int *)(iVar8 + 0x40) != 0) {
        XLockDisplay();
        iVar4 = XPending(*(undefined4 *)(iVar8 + 0x40));
        if (iVar4 != 0) {
          XNextEvent(*(undefined4 *)(iVar8 + 0x40),local_a0);
          XUnlockDisplay(*(undefined4 *)(iVar8 + 0x40));
          if (local_a0[0] == 0x1e) {
            if (local_90 == *(int *)(DAT_0069b940 + 0x58)) {
              if (*(code **)(DAT_0069b940 + 100) == (code *)0x0) {
                return 1;
              }
              (**(code **)(DAT_0069b940 + 100))(local_a0);
              return 1;
            }
          }
          else if (local_90 == *(int *)(DAT_0069b940 + 0x58)) {
            return 1;
          }
          if (*(code **)(iVar8 + 0x68) == (code *)0x0) {
            return 1;
          }
          (**(code **)(iVar8 + 0x68))(local_a0);
          return 1;
        }
        XUnlockDisplay(*(undefined4 *)(iVar8 + 0x40));
      }
    }
    else {
      if (*(int *)(iVar8 + 0x40) != 0) {
        XLockDisplay();
        iVar4 = XPending(*(undefined4 *)(iVar8 + 0x40));
        if (iVar4 != 0) {
          XNextEvent(*(undefined4 *)(iVar8 + 0x40),local_100);
          XUnlockDisplay(*(undefined4 *)(iVar8 + 0x40));
          if (local_100[0] == 0x1e) {
            if (local_f0 == *(int *)(DAT_0069b940 + 0x58)) {
              if (*(code **)(DAT_0069b940 + 100) == (code *)0x0) {
                return 1;
              }
              (**(code **)(DAT_0069b940 + 100))(local_100);
              return 1;
            }
          }
          else if (local_f0 == *(int *)(DAT_0069b940 + 0x58)) {
            return 1;
          }
          if (*(code **)(iVar8 + 0x68) == (code *)0x0) {
            return 1;
          }
          (**(code **)(iVar8 + 0x68))(local_100);
          return 1;
        }
        XUnlockDisplay(*(undefined4 *)(iVar8 + 0x40));
      }
      pthread_mutex_lock(__mutex);
      if (0 < *(int *)((int)__mutex + 0x2c)) {
        *(int *)((int)__mutex + 0x2c) = *(int *)((int)__mutex + 0x2c) + -1;
        pthread_mutex_unlock(__mutex);
        read(*(int *)((int)__mutex + 0x28),&uStack_31,1);
        pthread_mutex_lock(__mutex);
      }
      iVar4 = *(int *)((int)__mutex + 0x20);
      if (iVar4 == 0) {
        piVar12 = (int *)0x0;
LAB_0069b8d0:
        pthread_mutex_unlock(__mutex);
      }
      else {
        puVar13 = *(undefined4 **)(__mutex + 1);
        piVar12 = (int *)*puVar13;
        if (piVar12 != (int *)0x0) {
          piVar10 = piVar12 + 1;
          DataMemoryBarrier(0xf);
          do {
            bVar2 = (bool)hasExclusiveAccess(piVar10);
          } while (!bVar2);
          *piVar10 = *piVar10 + 1;
          DataMemoryBarrier(0xf);
          DataMemoryBarrier(0xf);
          do {
            iVar4 = *piVar10;
            bVar2 = (bool)hasExclusiveAccess(piVar10);
          } while (!bVar2);
          *piVar10 = iVar4 + -1;
          DataMemoryBarrier(0xf);
          if (iVar4 + -1 == 0) {
            (**(code **)(*piVar12 + 4))(piVar12);
          }
          iVar4 = *(int *)((int)__mutex + 0x20);
        }
        iVar4 = iVar4 + -1;
        *(int *)((int)__mutex + 0x20) = iVar4;
        if (0 < iVar4) {
          memmove(puVar13,puVar13 + 1,iVar4 * 4);
          iVar4 = *(int *)((int)__mutex + 0x20);
        }
        if ((*(int *)((int)__mutex + 0x1c) <= iVar4 * 2) || (*(int *)((int)__mutex + 0x1c) <= iVar4)
           ) goto LAB_0069b8d0;
        pvVar5 = (void *)__mutex[1].__data.__lock;
        if (iVar4 < 1) {
          free(pvVar5);
          *(int *)((int)__mutex + 0x1c) = iVar4;
          __mutex[1].__data.__lock = 0;
        }
        else {
          if (pvVar5 == (void *)0x0) {
            pvVar5 = malloc(iVar4 << 2);
            __mutex[1].__data.__lock = (int)pvVar5;
          }
          else {
            pvVar5 = realloc(pvVar5,iVar4 << 2);
            __mutex[1].__data.__lock = (int)pvVar5;
          }
          *(int *)((int)__mutex + 0x1c) = iVar4;
        }
        pthread_mutex_unlock(__mutex);
      }
      if (piVar12 != (int *)0x0) {
        (**(code **)(*piVar12 + 8))(piVar12);
        piVar10 = piVar12 + 1;
        DataMemoryBarrier(0xf);
        do {
          iVar8 = *piVar10;
          bVar2 = (bool)hasExclusiveAccess(piVar10);
        } while (!bVar2);
        *piVar10 = iVar8 + -1;
        DataMemoryBarrier(0xf);
        if (iVar8 + -1 == 0) {
          (**(code **)(*piVar12 + 4))(piVar12);
        }
        return 1;
      }
    }
    if (param_1 != 0) {
      return 0;
    }
    pthread_mutex_lock(__mutex);
    iVar4 = *(int *)((int)__mutex + 0x20);
    pthread_mutex_unlock(__mutex);
    if (iVar4 != 0) goto LAB_0069b6a4;
    if (*(int *)(iVar8 + 0x40) == 0) {
      iVar4 = 0;
    }
    else {
      XLockDisplay();
      iVar4 = XPending(*(undefined4 *)(iVar8 + 0x40));
      if (iVar4 != 0) break;
      XUnlockDisplay(*(undefined4 *)(iVar8 + 0x40));
      iVar4 = *(int *)(iVar8 + 0x40);
    }
    iVar11 = *(int *)((int)__mutex + 0x28);
    local_180.fds_bits[0] = 0;
    local_180.fds_bits[1] = 0;
    local_180.fds_bits[2] = 0;
    local_180.fds_bits[3] = 0;
    local_180.fds_bits[4] = 0;
    local_180.fds_bits[5] = 0;
    iVar6 = iVar11 + 0x1f;
    if (-1 < iVar11) {
      iVar6 = iVar11;
    }
    local_180.fds_bits[6] = 0;
    local_180.fds_bits[7] = 0;
    local_180.fds_bits[8] = 0;
    local_180.fds_bits[9] = 0;
    local_180.fds_bits[10] = 0;
    local_180.fds_bits[0xb] = 0;
    local_180.fds_bits[0xc] = 0;
    local_180.fds_bits[0xd] = 0;
    local_180.fds_bits[0xe] = 0;
    local_180.fds_bits[0xf] = 0;
    local_180.fds_bits[0x10] = 0;
    local_180.fds_bits[0x11] = 0;
    local_180.fds_bits[0x12] = 0;
    local_180.fds_bits[0x13] = 0;
    local_180.fds_bits[0x14] = 0;
    local_180.fds_bits[0x15] = 0;
    local_180.fds_bits[0x16] = 0;
    local_180.fds_bits[0x17] = 0;
    local_180.fds_bits[0x18] = 0;
    local_180.fds_bits[0x19] = 0;
    local_180.fds_bits[0x1a] = 0;
    local_180.fds_bits[0x1b] = 0;
    local_180.fds_bits[0x1c] = 0;
    local_180.fds_bits[0x1d] = 0;
    local_180.fds_bits[0x1e] = 0;
    local_180.fds_bits[0x1f] = 0;
    local_40 = tVar3;
    local_180.fds_bits[iVar6 >> 5] = local_180.fds_bits[iVar6 >> 5] | 1 << (iVar11 % 0x20 & 0xffU);
    if (iVar4 != 0) {
      XLockDisplay();
      iVar6 = XConnectionNumber(*(undefined4 *)(iVar8 + 0x40));
      iVar4 = iVar6 + 0x1f;
      if (-1 < iVar6) {
        iVar4 = iVar6;
      }
      if (iVar11 < iVar6) {
        iVar11 = iVar6;
      }
      uVar7 = *(undefined4 *)(iVar8 + 0x40);
      local_180.fds_bits[iVar4 >> 5] = local_180.fds_bits[iVar4 >> 5] | 1 << (iVar6 % 0x20 & 0xffU);
      XUnlockDisplay(uVar7);
    }
    select(iVar11 + 1,&local_180,(fd_set *)0x0,(fd_set *)0x0,&local_40);
    cVar1 = *(char *)(iVar8 + 0x60);
  } while( true );
  XUnlockDisplay(*(undefined4 *)(iVar8 + 0x40));
  goto LAB_0069b6a4;
}

