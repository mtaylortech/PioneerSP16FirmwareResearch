/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_004f6afc(int param_1,int param_2,int *param_3)

{
  bool bVar1;
  pthread_t pVar2;
  int iVar3;
  int *piVar4;
  int *piVar5;
  void *pvVar6;
  int iVar7;
  pthread_t pVar8;
  uint __size;
  int iVar9;
  
  pVar2 = pthread_self();
  iVar3 = FUN_00696cf4();
  if (iVar3 == 0) {
    pVar8 = 0;
  }
  else {
    pVar8 = *(pthread_t *)(iVar3 + 8);
  }
  if (pVar2 == pVar8) {
    iVar9 = *(int *)(param_1 + 0x34);
    iVar7 = iVar9 + 1;
    iVar3 = param_3[1];
    *(int *)(param_1 + 0x38) = *param_3;
    *(int *)(param_1 + 0x3c) = iVar3;
    if (((int)*(uint *)(param_1 + 0x30) < iVar7) &&
       (__size = iVar7 + iVar7 / 2 + 8U & 0xfffffff8, *(uint *)(param_1 + 0x30) != __size)) {
      pvVar6 = *(void **)(param_1 + 0x2c);
      if ((int)__size < 1) {
        free(pvVar6);
        iVar9 = *(int *)(param_1 + 0x34);
        pvVar6 = (void *)0x0;
        *(uint *)(param_1 + 0x30) = __size;
        *(undefined4 *)(param_1 + 0x2c) = 0;
        iVar7 = iVar9 + 1;
      }
      else {
        if (pvVar6 == (void *)0x0) {
          pvVar6 = malloc(__size);
          *(void **)(param_1 + 0x2c) = pvVar6;
        }
        else {
          pvVar6 = realloc(pvVar6,__size);
          iVar9 = *(int *)(param_1 + 0x34);
          iVar7 = iVar9 + 1;
          *(void **)(param_1 + 0x2c) = pvVar6;
        }
        *(uint *)(param_1 + 0x30) = __size;
      }
    }
    else {
      pvVar6 = *(void **)(param_1 + 0x2c);
    }
    *(int *)(param_1 + 0x34) = iVar7;
    if ((int)pvVar6 + iVar9 != 0) {
      *(undefined1 *)((int)pvVar6 + iVar9) = 1;
    }
    return;
  }
  iVar9 = *param_3;
  iVar3 = param_3[1];
  piVar4 = operator_new(0x28);
  piVar5 = DAT_004f6d38;
  *piVar4 = DAT_004f6d34;
  piVar4[9] = 0x5e715e28;
  DataMemoryBarrier(0xf);
  do {
    iVar7 = *piVar5;
    bVar1 = (bool)hasExclusiveAccess(piVar5);
  } while (!bVar1);
  *piVar5 = iVar7 + 1;
  DataMemoryBarrier(0xf);
  piVar4[1] = iVar7 + 1;
  FUN_00696c6c(piVar4 + 2);
  iVar7 = DAT_004f6d3c;
  piVar4[8] = param_2;
  *(undefined1 *)(piVar4 + 4) = 0;
  *piVar4 = iVar7 + 0x40;
  piVar4[2] = iVar7 + 0x58;
  piVar4[5] = param_1;
  piVar4[6] = iVar9;
  piVar4[7] = iVar3;
  pVar2 = pthread_self();
  pVar8 = (**(code **)(*(int *)(param_1 + 0x18) + 8))(param_1 + 0x18);
  if (pVar2 == pVar8) {
    if (((char)piVar4[4] == '\0') || (piVar4[1] != 0)) {
      (**(code **)(*piVar4 + 8))(piVar4);
    }
    (**(code **)(*piVar4 + 4))(piVar4);
    return;
  }
  iVar3 = (**(code **)(*(int *)(param_1 + 0x18) + 0x10))(param_1 + 0x18,piVar4,0);
  if (iVar3 == 0) {
    return;
  }
  piVar5 = *(int **)(param_1 + 0x20);
  if (piVar5 == (int *)0x0) {
    return;
  }
  if ((((uint)piVar5 & 3) == 0) && (piVar5[1] == 0x5e715e28)) {
    (**(code **)(*piVar5 + 8))();
    return;
  }
  FUN_004f782c(DAT_004f6d40,DAT_004f6d44,DAT_004f6d48);
  *(undefined4 *)(param_1 + 0x20) = 0;
  return;
}

