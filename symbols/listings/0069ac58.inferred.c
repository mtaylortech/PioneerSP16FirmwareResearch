/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_0069ac58(int param_1)

{
  bool bVar1;
  int iVar2;
  pthread_t pVar3;
  int iVar4;
  int *piVar5;
  void *__ptr;
  int iVar6;
  int *piVar7;
  void *pvVar8;
  
  pVar3 = pthread_self();
  iVar2 = DAT_0069ade0;
  if (pVar3 == *(pthread_t *)(param_1 + 8)) {
    return;
  }
  *(pthread_t *)(param_1 + 8) = pVar3;
  pvVar8 = *(void **)(iVar2 + 0x50);
  if (pvVar8 != (void *)0x0) {
    iVar4 = *(int *)((int)pvVar8 + 0x24);
    *(undefined4 *)(iVar2 + 0x50) = 0;
    close(iVar4);
    close(*(int *)((int)pvVar8 + 0x28));
    if (pvVar8 == *(void **)(iVar2 + 0x50)) {
      *(undefined4 *)(iVar2 + 0x50) = 0;
    }
    do {
      iVar6 = *(int *)((int)pvVar8 + 0x20);
      iVar4 = (iVar6 + -1) * 4;
      do {
        if (iVar6 < 1) {
          __ptr = *(void **)((int)pvVar8 + 0x18);
          if (*(int *)((int)pvVar8 + 0x1c) != 0) {
            free(__ptr);
            __ptr = (void *)0x0;
            *(undefined4 *)((int)pvVar8 + 0x18) = 0;
            *(undefined4 *)((int)pvVar8 + 0x1c) = 0;
          }
          free(__ptr);
          FUN_00644cf4(pvVar8);
          operator_delete(pvVar8);
          goto LAB_0069ad24;
        }
        iVar6 = iVar6 + -1;
        *(int *)((int)pvVar8 + 0x20) = iVar6;
        piVar5 = *(int **)(*(int *)((int)pvVar8 + 0x18) + iVar4);
        iVar4 = iVar4 + -4;
      } while (piVar5 == (int *)0x0);
      piVar7 = piVar5 + 1;
      DataMemoryBarrier(0xf);
      do {
        iVar4 = *piVar7;
        bVar1 = (bool)hasExclusiveAccess(piVar7);
      } while (!bVar1);
      *piVar7 = iVar4 + -1;
      DataMemoryBarrier(0xf);
      if (iVar4 + -1 == 0) {
        (**(code **)(*piVar5 + 4))();
      }
    } while( true );
  }
LAB_0069ad24:
  iVar4 = DAT_0069ade0;
  if ((*(int *)(iVar2 + 0x40) != 0) && (*(char *)(DAT_0069ade0 + 0x60) == '\0')) {
    XDestroyWindow(*(int *)(iVar2 + 0x40),*(undefined4 *)(DAT_0069ade0 + 0x58));
    XCloseDisplay(*(undefined4 *)(iVar4 + 0x40));
    *(undefined4 *)(iVar4 + 0x58) = 0;
    *(undefined4 *)(iVar4 + 0x40) = 0;
    if (*(int *)(iVar4 + 0x3c) != 0) {
      XSetIOErrorHandler(*(undefined4 *)(iVar4 + 0x44));
      *(undefined4 *)(iVar4 + 0x44) = 0;
      XSetErrorHandler(*(undefined4 *)(iVar4 + 0x48));
      *(undefined4 *)(iVar4 + 0x48) = 0;
    }
  }
  juce_x11_queue_bootstrap_00697fc0();
  return;
}

