/* INFERRED PSEUDOCODE; names/types/indirect targets need instruction checks. No target execution. */

void FUN_00698ad0(int param_1)

{
  bool bVar1;
  undefined4 uVar2;
  int *piVar3;
  undefined4 *puVar4;
  int iVar5;
  int *piVar6;
  undefined4 *puVar7;
  int *piVar8;
  
  piVar3 = operator_new(0x10);
  iVar5 = DAT_00698c74;
  piVar3[1] = 0;
  *piVar3 = iVar5;
  if (param_1 == 0) {
    piVar3[2] = 0;
  }
  else {
    puVar4 = *(undefined4 **)(param_1 + 4);
    if (puVar4 == (undefined4 *)0x0) {
      puVar4 = operator_new(0xc);
      uVar2 = DAT_00698c7c;
      puVar7 = *(undefined4 **)(param_1 + 4);
      puVar4[1] = 0;
      puVar4[2] = param_1;
      *puVar4 = uVar2;
      if (puVar4 != puVar7) {
        piVar8 = puVar4 + 1;
        DataMemoryBarrier(0xf);
        do {
          bVar1 = (bool)hasExclusiveAccess(piVar8);
        } while (!bVar1);
        *piVar8 = *piVar8 + 1;
        DataMemoryBarrier(0xf);
        piVar8 = *(int **)(param_1 + 4);
        *(undefined4 **)(param_1 + 4) = puVar4;
        if (piVar8 != (int *)0x0) {
          piVar6 = piVar8 + 1;
          DataMemoryBarrier(0xf);
          do {
            iVar5 = *piVar6;
            bVar1 = (bool)hasExclusiveAccess(piVar6);
          } while (!bVar1);
          *piVar6 = iVar5 + -1;
          DataMemoryBarrier(0xf);
          if (iVar5 + -1 == 0) {
            (**(code **)(*piVar8 + 4))(piVar8);
          }
          puVar4 = *(undefined4 **)(param_1 + 4);
        }
      }
      piVar3[2] = (int)puVar4;
      if (puVar4 == (undefined4 *)0x0) goto LAB_00698b34;
    }
    else {
      piVar3[2] = (int)puVar4;
    }
    piVar8 = puVar4 + 1;
    DataMemoryBarrier(0xf);
    do {
      bVar1 = (bool)hasExclusiveAccess(piVar8);
    } while (!bVar1);
    *piVar8 = *piVar8 + 1;
    DataMemoryBarrier(0xf);
  }
LAB_00698b34:
  *(undefined1 *)(piVar3 + 3) = 0;
  if (((*(int *)(DAT_00698c78 + 4) != 0) && (*(char *)(*(int *)(DAT_00698c78 + 4) + 4) == '\0')) &&
     (iVar5 = FUN_006986a0(piVar3), iVar5 != 0)) {
    return;
  }
  piVar8 = piVar3 + 1;
  DataMemoryBarrier(0xf);
  do {
    bVar1 = (bool)hasExclusiveAccess(piVar8);
  } while (!bVar1);
  *piVar8 = *piVar8 + 1;
  DataMemoryBarrier(0xf);
  DataMemoryBarrier(0xf);
  do {
    iVar5 = *piVar8;
    bVar1 = (bool)hasExclusiveAccess(piVar8);
  } while (!bVar1);
  *piVar8 = iVar5 + -1;
  DataMemoryBarrier(0xf);
  if (iVar5 + -1 != 0) {
    return;
  }
  (**(code **)(*piVar3 + 4))(piVar3);
  return;
}

