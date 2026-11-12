/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

undefined4 FUN_006986a0(int param_1)

{
  bool bVar1;
  undefined4 uVar2;
  void *pvVar3;
  pthread_mutex_t *__mutex;
  int *piVar4;
  uint uVar5;
  int iVar6;
  int iVar7;
  undefined1 local_21 [5];
  
  if (*(char *)(DAT_006987f4 + 0x60) == '\0') {
    __mutex = *(pthread_mutex_t **)(DAT_006987f4 + 0x50);
    pthread_mutex_lock(__mutex);
    iVar7 = *(int *)((int)__mutex + 0x20);
    iVar6 = iVar7 + 1;
    if (((int)*(uint *)((int)__mutex + 0x1c) < iVar6) &&
       (uVar5 = iVar6 + iVar6 / 2 + 8U & 0xfffffff8, *(uint *)((int)__mutex + 0x1c) != uVar5)) {
      pvVar3 = (void *)__mutex[1].__data.__lock;
      if ((int)uVar5 < 1) {
        free(pvVar3);
        iVar7 = *(int *)((int)__mutex + 0x20);
        __mutex[1].__data.__lock = 0;
        iVar6 = iVar7 + 1;
        *(uint *)((int)__mutex + 0x1c) = uVar5;
        pvVar3 = (void *)0x0;
      }
      else {
        if (pvVar3 == (void *)0x0) {
          pvVar3 = malloc(uVar5 << 2);
          __mutex[1].__data.__lock = (int)pvVar3;
        }
        else {
          pvVar3 = realloc(pvVar3,uVar5 << 2);
          iVar7 = *(int *)((int)__mutex + 0x20);
          iVar6 = iVar7 + 1;
          __mutex[1].__data.__lock = (int)pvVar3;
        }
        *(uint *)((int)__mutex + 0x1c) = uVar5;
      }
    }
    else {
      pvVar3 = (void *)__mutex[1].__data.__lock;
    }
    *(int *)((int)__mutex + 0x20) = iVar6;
    *(int *)((int)pvVar3 + iVar7 * 4) = param_1;
    if (param_1 != 0) {
      piVar4 = (int *)(param_1 + 4);
      DataMemoryBarrier(0xf);
      do {
        bVar1 = (bool)hasExclusiveAccess(piVar4);
      } while (!bVar1);
      *piVar4 = *piVar4 + 1;
      DataMemoryBarrier(0xf);
    }
    if (*(int *)((int)__mutex + 0x2c) < 0x80) {
      *(int *)((int)__mutex + 0x2c) = *(int *)((int)__mutex + 0x2c) + 1;
      pthread_mutex_unlock(__mutex);
      local_21[0] = 0xff;
      write(*(int *)((int)__mutex + 0x24),local_21,1);
      pthread_mutex_lock(__mutex);
    }
    pthread_mutex_unlock(__mutex);
    uVar2 = 1;
  }
  else {
    uVar2 = 0;
  }
  return uVar2;
}

