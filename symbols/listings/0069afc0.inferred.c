/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

/* WARNING: Unknown calling convention -- yet parameter storage is locked */
/* SUPPORTED ANALYST INTERPRETATION; address identity retained. XPending/XNextEvent and
   mutex-protected internal virtual callbacks, select wait, exit flag +5. Original source signature
   is not recovered. */

void juce_x11_message_dispatch_0069afc0(MessageManager_view_0069826c *manager)

{
  byte bVar1;
  bool bVar2;
  timeval tVar3;
  int iVar4;
  void *pvVar5;
  int iVar6;
  undefined4 uVar7;
  uint uVar8;
  int *piVar9;
  pthread_mutex_t *__mutex;
  int iVar10;
  int *piVar11;
  undefined4 *puVar12;
  int iVar13;
  fd_set local_188;
  int local_108 [4];
  int local_f8;
  int local_a8 [4];
  int local_98;
  timeval local_48;
  undefined1 auStack_39 [5];
  
  iVar4 = DAT_0069b398;
  tVar3 = DAT_0069b390;
  FUN_00639188();
LAB_0069b04c:
  bVar1 = manager->dispatch_exit_flag;
joined_r0x0069b054:
  if (bVar1 != 0) {
    return;
  }
LAB_0069b05c:
  if (*(char *)(iVar4 + 0x60) != '\0') {
LAB_0069b5b0:
    sleep_milliseconds_006457dc(1);
    goto LAB_0069b04c;
  }
  if (*(char *)(iVar4 + 8) != '\0') {
    DAT_00f6e6a4 = 1;
    if (DAT_00f6e680 != 0) {
      FUN_0064582c();
    }
    goto LAB_0069b5b0;
  }
  __mutex = *(pthread_mutex_t **)(iVar4 + 0x50);
  uVar8 = __mutex[2].__data.__lock + 1;
  __mutex[2].__data.__lock = uVar8;
  if ((uVar8 & 1) == 0) {
    pthread_mutex_lock(__mutex);
    if (0 < *(int *)((int)__mutex + 0x2c)) {
      *(int *)((int)__mutex + 0x2c) = *(int *)((int)__mutex + 0x2c) + -1;
      pthread_mutex_unlock(__mutex);
      read(*(int *)((int)__mutex + 0x28),auStack_39,1);
      pthread_mutex_lock(__mutex);
    }
    iVar13 = *(int *)((int)__mutex + 0x20);
    if (iVar13 == 0) {
      pthread_mutex_unlock(__mutex);
    }
    else {
      puVar12 = *(undefined4 **)(__mutex + 1);
      piVar11 = (int *)*puVar12;
      if (piVar11 != (int *)0x0) {
        piVar9 = piVar11 + 1;
        DataMemoryBarrier(0xf);
        do {
          bVar2 = (bool)hasExclusiveAccess(piVar9);
        } while (!bVar2);
        *piVar9 = *piVar9 + 1;
        DataMemoryBarrier(0xf);
        DataMemoryBarrier(0xf);
        do {
          iVar13 = *piVar9;
          bVar2 = (bool)hasExclusiveAccess(piVar9);
        } while (!bVar2);
        *piVar9 = iVar13 + -1;
        DataMemoryBarrier(0xf);
        if (iVar13 + -1 == 0) {
          (**(code **)(*piVar11 + 4))(piVar11);
        }
        iVar13 = *(int *)((int)__mutex + 0x20);
      }
      iVar13 = iVar13 + -1;
      *(int *)((int)__mutex + 0x20) = iVar13;
      if (0 < iVar13) {
        memmove(puVar12,puVar12 + 1,iVar13 * 4);
        iVar13 = *(int *)((int)__mutex + 0x20);
      }
      if ((iVar13 * 2 < *(int *)((int)__mutex + 0x1c)) && (iVar13 < *(int *)((int)__mutex + 0x1c)))
      {
        pvVar5 = (void *)__mutex[1].__data.__lock;
        if (iVar13 < 1) {
          free(pvVar5);
          __mutex[1].__data.__lock = 0;
        }
        else if (pvVar5 == (void *)0x0) {
          pvVar5 = malloc(iVar13 << 2);
          __mutex[1].__data.__lock = (int)pvVar5;
        }
        else {
          pvVar5 = realloc(pvVar5,iVar13 << 2);
          __mutex[1].__data.__lock = (int)pvVar5;
        }
        *(int *)((int)__mutex + 0x1c) = iVar13;
      }
      pthread_mutex_unlock(__mutex);
      if (piVar11 != (int *)0x0) goto LAB_0069b1b0;
    }
    if (*(int *)(iVar4 + 0x40) != 0) {
      XLockDisplay();
      iVar13 = XPending(*(undefined4 *)(iVar4 + 0x40));
      if (iVar13 != 0) {
        XNextEvent(*(undefined4 *)(iVar4 + 0x40),local_a8);
        XUnlockDisplay(*(undefined4 *)(iVar4 + 0x40));
        if (local_a8[0] == 0x1e) {
          if (local_98 == *(int *)(iVar4 + 0x58)) {
            if (*(code **)(iVar4 + 100) != (code *)0x0) {
              (**(code **)(iVar4 + 100))(local_a8);
            }
            goto LAB_0069b04c;
          }
        }
        else if (local_98 == *(int *)(iVar4 + 0x58)) goto LAB_0069b04c;
        if (*(code **)(iVar4 + 0x68) != (code *)0x0) {
          (**(code **)(iVar4 + 0x68))(local_a8);
        }
        goto LAB_0069b04c;
      }
      XUnlockDisplay(*(undefined4 *)(iVar4 + 0x40));
    }
  }
  else {
    if (*(int *)(iVar4 + 0x40) != 0) {
      XLockDisplay();
      iVar13 = XPending(*(undefined4 *)(iVar4 + 0x40));
      if (iVar13 != 0) {
        XNextEvent(*(undefined4 *)(iVar4 + 0x40),local_108);
        XUnlockDisplay(*(undefined4 *)(iVar4 + 0x40));
        if (local_108[0] == 0x1e) {
          if (local_f8 == *(int *)(iVar4 + 0x58)) {
            if (*(code **)(iVar4 + 100) != (code *)0x0) {
              (**(code **)(iVar4 + 100))(local_108);
            }
            goto LAB_0069b04c;
          }
        }
        else if (local_f8 == *(int *)(iVar4 + 0x58)) goto LAB_0069b04c;
        if (*(code **)(iVar4 + 0x68) != (code *)0x0) {
          (**(code **)(iVar4 + 0x68))(local_108);
        }
        goto LAB_0069b04c;
      }
      XUnlockDisplay(*(undefined4 *)(iVar4 + 0x40));
    }
    pthread_mutex_lock(__mutex);
    if (0 < *(int *)((int)__mutex + 0x2c)) {
      *(int *)((int)__mutex + 0x2c) = *(int *)((int)__mutex + 0x2c) + -1;
      pthread_mutex_unlock(__mutex);
      read(*(int *)((int)__mutex + 0x28),auStack_39,1);
      pthread_mutex_lock(__mutex);
    }
    iVar13 = *(int *)((int)__mutex + 0x20);
    if (iVar13 == 0) {
      piVar11 = (int *)0x0;
    }
    else {
      puVar12 = *(undefined4 **)(__mutex + 1);
      piVar11 = (int *)*puVar12;
      if (piVar11 != (int *)0x0) {
        piVar9 = piVar11 + 1;
        DataMemoryBarrier(0xf);
        do {
          bVar2 = (bool)hasExclusiveAccess(piVar9);
        } while (!bVar2);
        *piVar9 = *piVar9 + 1;
        DataMemoryBarrier(0xf);
        DataMemoryBarrier(0xf);
        do {
          iVar13 = *piVar9;
          bVar2 = (bool)hasExclusiveAccess(piVar9);
        } while (!bVar2);
        *piVar9 = iVar13 + -1;
        DataMemoryBarrier(0xf);
        if (iVar13 + -1 == 0) {
          (**(code **)(*piVar11 + 4))(piVar11);
        }
        iVar13 = *(int *)((int)__mutex + 0x20);
      }
      iVar13 = iVar13 + -1;
      *(int *)((int)__mutex + 0x20) = iVar13;
      if (0 < iVar13) {
        memmove(puVar12,puVar12 + 1,iVar13 * 4);
        iVar13 = *(int *)((int)__mutex + 0x20);
      }
      if ((iVar13 * 2 < *(int *)((int)__mutex + 0x1c)) && (iVar13 < *(int *)((int)__mutex + 0x1c)))
      {
        pvVar5 = (void *)__mutex[1].__data.__lock;
        if (iVar13 < 1) {
          free(pvVar5);
          __mutex[1].__data.__lock = 0;
        }
        else if (pvVar5 == (void *)0x0) {
          pvVar5 = malloc(iVar13 << 2);
          __mutex[1].__data.__lock = (int)pvVar5;
        }
        else {
          pvVar5 = realloc(pvVar5,iVar13 << 2);
          __mutex[1].__data.__lock = (int)pvVar5;
        }
        *(int *)((int)__mutex + 0x1c) = iVar13;
      }
    }
    pthread_mutex_unlock(__mutex);
    if (piVar11 != (int *)0x0) {
      (**(code **)(*piVar11 + 8))(piVar11);
      piVar9 = piVar11 + 1;
      DataMemoryBarrier(0xf);
      do {
        iVar13 = *piVar9;
        bVar2 = (bool)hasExclusiveAccess(piVar9);
      } while (!bVar2);
      *piVar9 = iVar13 + -1;
      DataMemoryBarrier(0xf);
      if (iVar13 + -1 == 0) {
        (**(code **)(*piVar11 + 4))(piVar11);
      }
      goto LAB_0069b04c;
    }
  }
  pthread_mutex_lock(__mutex);
  iVar13 = *(int *)((int)__mutex + 0x20);
  pthread_mutex_unlock(__mutex);
  if (iVar13 == 0) {
    iVar13 = 0;
    if (*(int *)(iVar4 + 0x40) != 0) {
      XLockDisplay();
      iVar13 = XPending(*(undefined4 *)(iVar4 + 0x40));
      if (iVar13 != 0) {
        XUnlockDisplay(*(undefined4 *)(iVar4 + 0x40));
        goto LAB_0069b05c;
      }
      XUnlockDisplay(*(undefined4 *)(iVar4 + 0x40));
      iVar13 = *(int *)(iVar4 + 0x40);
    }
    iVar10 = *(int *)((int)__mutex + 0x28);
    local_188.fds_bits[0] = 0;
    local_188.fds_bits[1] = 0;
    local_188.fds_bits[2] = 0;
    local_188.fds_bits[3] = 0;
    local_188.fds_bits[4] = 0;
    local_188.fds_bits[5] = 0;
    iVar6 = iVar10 + 0x1f;
    if (-1 < iVar10) {
      iVar6 = iVar10;
    }
    local_188.fds_bits[6] = 0;
    local_188.fds_bits[7] = 0;
    local_188.fds_bits[8] = 0;
    local_188.fds_bits[9] = 0;
    local_188.fds_bits[10] = 0;
    local_188.fds_bits[0xb] = 0;
    local_188.fds_bits[0xc] = 0;
    local_188.fds_bits[0xd] = 0;
    local_188.fds_bits[0xe] = 0;
    local_188.fds_bits[0xf] = 0;
    local_188.fds_bits[0x10] = 0;
    local_188.fds_bits[0x11] = 0;
    local_188.fds_bits[0x12] = 0;
    local_188.fds_bits[0x13] = 0;
    local_188.fds_bits[0x14] = 0;
    local_188.fds_bits[0x15] = 0;
    local_188.fds_bits[0x16] = 0;
    local_188.fds_bits[0x17] = 0;
    local_188.fds_bits[0x18] = 0;
    local_188.fds_bits[0x19] = 0;
    local_188.fds_bits[0x1a] = 0;
    local_188.fds_bits[0x1b] = 0;
    local_188.fds_bits[0x1c] = 0;
    local_188.fds_bits[0x1d] = 0;
    local_188.fds_bits[0x1e] = 0;
    local_188.fds_bits[0x1f] = 0;
    local_48 = tVar3;
    local_188.fds_bits[iVar6 >> 5] = local_188.fds_bits[iVar6 >> 5] | 1 << (iVar10 % 0x20 & 0xffU);
    if (iVar13 != 0) {
      XLockDisplay();
      iVar6 = XConnectionNumber(*(undefined4 *)(iVar4 + 0x40));
      iVar13 = iVar6 + 0x1f;
      if (-1 < iVar6) {
        iVar13 = iVar6;
      }
      if (iVar10 < iVar6) {
        iVar10 = iVar6;
      }
      uVar7 = *(undefined4 *)(iVar4 + 0x40);
      local_188.fds_bits[iVar13 >> 5] =
           local_188.fds_bits[iVar13 >> 5] | 1 << (iVar6 % 0x20 & 0xffU);
      XUnlockDisplay(uVar7);
    }
    select(iVar10 + 1,&local_188,(fd_set *)0x0,(fd_set *)0x0,&local_48);
  }
  goto LAB_0069b05c;
LAB_0069b1b0:
  (**(code **)(*piVar11 + 8))(piVar11);
  piVar9 = piVar11 + 1;
  DataMemoryBarrier(0xf);
  do {
    iVar13 = *piVar9;
    bVar2 = (bool)hasExclusiveAccess(piVar9);
  } while (!bVar2);
  *piVar9 = iVar13 + -1;
  DataMemoryBarrier(0xf);
  if (iVar13 + -1 != 0) goto LAB_0069b04c;
  (**(code **)(*piVar11 + 4))(piVar11);
  bVar1 = manager->dispatch_exit_flag;
  goto joined_r0x0069b054;
}

