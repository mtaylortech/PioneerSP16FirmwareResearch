/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_0038d6e8(int param_1,int *param_2)

{
  uint *__ptr;
  void *pvVar1;
  uint uVar2;
  uint *puVar3;
  uint *puVar4;
  int iVar5;
  int iVar6;
  uint *puVar7;
  
  if ((param_2 != (int *)0x0) && (((uint)param_2 & 3) == 0)) {
    uVar2 = (int)param_2 + *(int *)(*param_2 + -0xc);
    if ((uVar2 != 0) &&
       (((uVar2 & 3) == 0 && (*(int *)((int)param_2 + *(int *)(*param_2 + -0xc)) == 0x5e715e28)))) {
      iVar5 = *(int *)(param_1 + 0x10);
      __ptr = *(uint **)(param_1 + 8);
      iVar6 = iVar5 * 4;
      puVar7 = __ptr + iVar5;
      if (__ptr != puVar7) {
        puVar3 = __ptr;
        puVar4 = __ptr;
        if ((int *)*__ptr == param_2) {
          return;
        }
        while (puVar7 != puVar4 + 1) {
          puVar3 = puVar3 + 1;
          puVar4 = puVar4 + 1;
          if ((int *)*puVar3 == param_2) {
            return;
          }
        }
      }
      iVar5 = iVar5 + 1;
      if (((int)*(uint *)(param_1 + 0xc) < iVar5) &&
         (uVar2 = iVar5 + iVar5 / 2 + 8U & 0xfffffff8, *(uint *)(param_1 + 0xc) != uVar2)) {
        if ((int)uVar2 < 1) {
          free(__ptr);
          pvVar1 = (void *)0x0;
          *(undefined4 *)(param_1 + 8) = 0;
          iVar5 = *(int *)(param_1 + 0x10) + 1;
          iVar6 = *(int *)(param_1 + 0x10) << 2;
        }
        else {
          if (__ptr == (uint *)0x0) {
            pvVar1 = malloc(uVar2 << 2);
          }
          else {
            pvVar1 = realloc(__ptr,uVar2 << 2);
            iVar5 = *(int *)(param_1 + 0x10) + 1;
            iVar6 = *(int *)(param_1 + 0x10) << 2;
          }
          *(void **)(param_1 + 8) = pvVar1;
        }
        *(uint *)(param_1 + 0xc) = uVar2;
        *(int *)(param_1 + 0x10) = iVar5;
        if ((uint *)((int)pvVar1 + iVar6) != (uint *)0x0) {
          *(uint *)((int)pvVar1 + iVar6) = (uint)param_2;
        }
        return;
      }
      *(int *)(param_1 + 0x10) = iVar5;
      if (puVar7 != (uint *)0x0) {
        *puVar7 = (uint)param_2;
      }
      return;
    }
  }
  FUN_004f782c(DAT_0038d828,DAT_0038d82c,DAT_0038d830);
  return;
}

