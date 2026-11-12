/* INFERRED PSEUDOCODE; names/types/indirect targets need instruction checks. No target execution. */

void FUN_0069a4e4(void)

{
  bool bVar1;
  int iVar2;
  int *piVar3;
  void *__ptr;
  int iVar4;
  int iVar5;
  int *piVar6;
  void *pvVar7;
  int *piVar8;
  
  iVar2 = DAT_0069a6b8;
  piVar8 = *(int **)(DAT_0069a6b8 + 4);
  if (piVar8 != (int *)0x0) {
    if ((int *)*piVar8 != (int *)0x0) {
      iVar4 = *(int *)*piVar8;
      *piVar8 = 0;
      (**(code **)(iVar4 + 4))();
    }
    pvVar7 = *(void **)(iVar2 + 0x50);
    if (pvVar7 != (void *)0x0) {
      iVar4 = *(int *)((int)pvVar7 + 0x24);
      *(undefined4 *)(DAT_0069a6b8 + 0x50) = 0;
      close(iVar4);
      close(*(int *)((int)pvVar7 + 0x28));
      if (pvVar7 == *(void **)(iVar2 + 0x50)) {
        *(undefined4 *)(DAT_0069a6b8 + 0x50) = 0;
      }
      do {
        iVar5 = *(int *)((int)pvVar7 + 0x20);
        iVar4 = (iVar5 + -1) * 4;
        do {
          if (iVar5 < 1) {
            __ptr = *(void **)((int)pvVar7 + 0x18);
            if (*(int *)((int)pvVar7 + 0x1c) != 0) {
              free(__ptr);
              __ptr = (void *)0x0;
              *(undefined4 *)((int)pvVar7 + 0x18) = 0;
              *(undefined4 *)((int)pvVar7 + 0x1c) = 0;
            }
            free(__ptr);
            FUN_00644cf4(pvVar7);
            operator_delete(pvVar7);
            goto LAB_0069a5c8;
          }
          iVar5 = iVar5 + -1;
          *(int *)((int)pvVar7 + 0x20) = iVar5;
          piVar3 = *(int **)(*(int *)((int)pvVar7 + 0x18) + iVar4);
          iVar4 = iVar4 + -4;
        } while (piVar3 == (int *)0x0);
        piVar6 = piVar3 + 1;
        DataMemoryBarrier(0xf);
        do {
          iVar4 = *piVar6;
          bVar1 = (bool)hasExclusiveAccess(piVar6);
        } while (!bVar1);
        *piVar6 = iVar4 + -1;
        DataMemoryBarrier(0xf);
        if (iVar4 + -1 == 0) {
          (**(code **)(*piVar3 + 4))();
        }
      } while( true );
    }
LAB_0069a5c8:
    iVar4 = DAT_0069a6b8;
    if ((*(int *)(iVar2 + 0x40) != 0) && (*(char *)(DAT_0069a6b8 + 0x60) == '\0')) {
      XDestroyWindow(*(int *)(iVar2 + 0x40),*(undefined4 *)(DAT_0069a6b8 + 0x58));
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
    *(undefined4 *)(iVar2 + 4) = 0;
    FUN_00644cf4(piVar8 + 4);
    if ((int *)*piVar8 != (int *)0x0) {
      (**(code **)(*(int *)*piVar8 + 4))();
    }
    operator_delete(piVar8);
  }
  *(undefined4 *)(iVar2 + 4) = 0;
  return;
}

