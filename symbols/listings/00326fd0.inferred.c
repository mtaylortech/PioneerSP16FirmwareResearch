/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_00326fd0(int param_1,int param_2,undefined4 param_3,int param_4,undefined4 param_5)

{
  int iVar1;
  bool bVar2;
  void *pvVar3;
  int *piVar4;
  int *piVar5;
  void *pvVar6;
  int iVar7;
  int *piVar8;
  void *local_40;
  undefined4 local_3c;
  int local_38;
  void *local_34;
  undefined1 auStack_2c [8];
  
  pvVar3 = operator_new(0x6d0);
  FUN_0026d4a4(pvVar3,param_2 + 0x88,param_5,*(undefined4 *)(param_1 + 0x44));
  *(void **)(param_4 + 0xc) = pvVar3;
  piVar4 = operator_new(0x2a0);
  FUN_00448d78(piVar4,param_3,param_4);
  if (pvVar3 == (void *)0x0) {
    iVar7 = 0;
  }
  else {
    iVar7 = (int)pvVar3 + 0xc;
  }
  FUN_00391b98(piVar4,iVar7);
  piVar5 = *(int **)((int)pvVar3 + 0x28);
  if (piVar4 != piVar5) {
    if (piVar4 != (int *)0x0) {
      piVar5 = piVar4 + 0x1d;
      DataMemoryBarrier(0xf);
      do {
        bVar2 = (bool)hasExclusiveAccess(piVar5);
      } while (!bVar2);
      *piVar5 = *piVar5 + 1;
      DataMemoryBarrier(0xf);
      piVar5 = *(int **)((int)pvVar3 + 0x28);
    }
    *(int **)((int)pvVar3 + 0x28) = piVar4;
    if (piVar5 != (int *)0x0) {
      piVar8 = piVar5 + 0x1d;
      DataMemoryBarrier(0xf);
      do {
        iVar7 = *piVar8;
        bVar2 = (bool)hasExclusiveAccess(piVar8);
      } while (!bVar2);
      *piVar8 = iVar7 + -1;
      DataMemoryBarrier(0xf);
      if (iVar7 + -1 == 0) {
        (**(code **)(*piVar5 + 4))();
      }
    }
  }
  piVar5 = *(int **)((int)pvVar3 + 0x128);
  if (piVar4 != piVar5) {
    if (piVar4 != (int *)0x0) {
      piVar5 = piVar4 + 0x1d;
      DataMemoryBarrier(0xf);
      do {
        bVar2 = (bool)hasExclusiveAccess(piVar5);
      } while (!bVar2);
      *piVar5 = *piVar5 + 1;
      DataMemoryBarrier(0xf);
      piVar5 = *(int **)((int)pvVar3 + 0x128);
    }
    *(int **)((int)pvVar3 + 0x128) = piVar4;
    if (piVar5 != (int *)0x0) {
      piVar8 = piVar5 + 0x1d;
      DataMemoryBarrier(0xf);
      do {
        iVar7 = *piVar8;
        bVar2 = (bool)hasExclusiveAccess(piVar8);
      } while (!bVar2);
      *piVar8 = iVar7 + -1;
      DataMemoryBarrier(0xf);
      if (iVar7 + -1 == 0) {
        (**(code **)(*piVar5 + 4))();
      }
    }
  }
  FUN_00392c2c(param_2,piVar4,0);
  FUN_0032a908(param_1 + 0x2c,pvVar3);
  FUN_0026c9d4(pvVar3,*(undefined4 *)(param_1 + 0x28));
  pvVar6 = operator_new(0x3c);
  FUN_001effec(pvVar6,param_2 + 0x88,*(undefined4 *)(param_1 + 0x44));
  FUN_00666e84(auStack_2c,DAT_003272dc);
  local_40 = (void *)0x0;
  local_3c = 0;
  local_38 = 0;
  local_34 = pvVar6;
  piVar4 = operator_new(0x114);
  FUN_003bd20c(piVar4,param_3,&local_40,auStack_2c);
  if (0 < local_38) {
    iVar7 = 0;
    do {
      iVar1 = iVar7 * 8;
      iVar7 = iVar7 + 1;
      FUN_006280c8((void *)((int)local_40 + iVar1));
    } while (iVar7 < local_38);
  }
  free(local_40);
  piVar5 = *(int **)((int)pvVar6 + 0x28);
  if (piVar4 != piVar5) {
    if (piVar4 != (int *)0x0) {
      piVar5 = piVar4 + 0x1d;
      DataMemoryBarrier(0xf);
      do {
        bVar2 = (bool)hasExclusiveAccess(piVar5);
      } while (!bVar2);
      *piVar5 = *piVar5 + 1;
      DataMemoryBarrier(0xf);
      piVar5 = *(int **)((int)pvVar6 + 0x28);
    }
    *(int **)((int)pvVar6 + 0x28) = piVar4;
    if (piVar5 != (int *)0x0) {
      piVar4 = piVar5 + 0x1d;
      DataMemoryBarrier(0xf);
      do {
        iVar7 = *piVar4;
        bVar2 = (bool)hasExclusiveAccess(piVar4);
      } while (!bVar2);
      *piVar4 = iVar7 + -1;
      DataMemoryBarrier(0xf);
      if (iVar7 + -1 == 0) {
        (**(code **)(*piVar5 + 4))();
      }
    }
  }
  FUN_0032a908(param_1 + 0x2c,pvVar6);
  FUN_006280c8(auStack_2c);
  FUN_0026c70c(pvVar3,pvVar6);
  return;
}

