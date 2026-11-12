/* INFERRED PSEUDOCODE; names/types/indirect targets need instruction checks. No target execution. */

void FUN_0069aa44(void)

{
  bool bVar1;
  undefined4 *puVar2;
  undefined4 *puVar3;
  int *piVar4;
  void *__ptr;
  int iVar5;
  int iVar6;
  int *piVar7;
  int *piVar8;
  void *pvVar9;
  
  puVar2 = DAT_0069ac54;
  piVar8 = (int *)*DAT_0069ac54;
  if (piVar8 != (int *)0x0) {
    FUN_00698384(piVar8);
    (**(code **)(*piVar8 + 4))(piVar8);
  }
  FUN_0069693c();
  piVar8 = (int *)puVar2[1];
  if (piVar8 != (int *)0x0) {
    if ((int *)*piVar8 != (int *)0x0) {
      iVar5 = *(int *)*piVar8;
      *piVar8 = 0;
      (**(code **)(iVar5 + 4))();
    }
    pvVar9 = (void *)puVar2[0x14];
    if (pvVar9 != (void *)0x0) {
      iVar5 = *(int *)((int)pvVar9 + 0x24);
      DAT_0069ac54[0x14] = 0;
      close(iVar5);
      close(*(int *)((int)pvVar9 + 0x28));
      if (pvVar9 == (void *)puVar2[0x14]) {
        DAT_0069ac54[0x14] = 0;
      }
      do {
        iVar6 = *(int *)((int)pvVar9 + 0x20);
        iVar5 = (iVar6 + -1) * 4;
        do {
          if (iVar6 < 1) {
            __ptr = *(void **)((int)pvVar9 + 0x18);
            if (*(int *)((int)pvVar9 + 0x1c) != 0) {
              free(__ptr);
              __ptr = (void *)0x0;
              *(undefined4 *)((int)pvVar9 + 0x18) = 0;
              *(undefined4 *)((int)pvVar9 + 0x1c) = 0;
            }
            free(__ptr);
            FUN_00644cf4(pvVar9);
            operator_delete(pvVar9);
            goto LAB_0069ab50;
          }
          iVar6 = iVar6 + -1;
          *(int *)((int)pvVar9 + 0x20) = iVar6;
          piVar4 = *(int **)(*(int *)((int)pvVar9 + 0x18) + iVar5);
          iVar5 = iVar5 + -4;
        } while (piVar4 == (int *)0x0);
        piVar7 = piVar4 + 1;
        DataMemoryBarrier(0xf);
        do {
          iVar5 = *piVar7;
          bVar1 = (bool)hasExclusiveAccess(piVar7);
        } while (!bVar1);
        *piVar7 = iVar5 + -1;
        DataMemoryBarrier(0xf);
        if (iVar5 + -1 == 0) {
          (**(code **)(*piVar4 + 4))();
        }
      } while( true );
    }
LAB_0069ab50:
    puVar3 = DAT_0069ac54;
    if ((puVar2[0x10] != 0) && (*(char *)(DAT_0069ac54 + 0x18) == '\0')) {
      XDestroyWindow(puVar2[0x10],DAT_0069ac54[0x16]);
      XCloseDisplay(puVar3[0x10]);
      puVar3[0x16] = 0;
      puVar3[0x10] = 0;
      if (puVar3[0xf] != 0) {
        XSetIOErrorHandler(puVar3[0x11]);
        puVar3[0x11] = 0;
        XSetErrorHandler(puVar3[0x12]);
        puVar3[0x12] = 0;
      }
    }
    puVar2[1] = 0;
    FUN_00644cf4(piVar8 + 4);
    if ((int *)*piVar8 != (int *)0x0) {
      (**(code **)(*(int *)*piVar8 + 4))();
    }
    operator_delete(piVar8);
  }
  puVar2[1] = 0;
  return;
}

