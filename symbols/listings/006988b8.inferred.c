/* INFERRED PSEUDOCODE; names/types/indirect targets need instruction checks. No target execution. */

void FUN_006988b8(int param_1,undefined4 param_2)

{
  bool bVar1;
  int iVar2;
  undefined4 uVar3;
  int *piVar4;
  undefined4 *puVar5;
  int iVar6;
  undefined4 *puVar7;
  int *piVar8;
  int *piVar9;
  int iVar10;
  int iVar11;
  int iVar12;
  
  pthread_mutex_lock((pthread_mutex_t *)(param_1 + 0x14));
  iVar2 = DAT_00698ab4;
  iVar10 = *(int *)(param_1 + 0x10) + -1;
  iVar11 = iVar10 * 4;
  do {
    if (iVar10 < 0) {
      pthread_mutex_unlock((pthread_mutex_t *)(param_1 + 0x14));
      return;
    }
    iVar12 = *(int *)(*(int *)(param_1 + 8) + iVar11);
    piVar4 = operator_new(0x14);
    puVar5 = *(undefined4 **)(param_1 + 4);
    *piVar4 = iVar2;
    piVar4[1] = 0;
    if (puVar5 == (undefined4 *)0x0) {
      puVar5 = operator_new(0xc);
      puVar7 = *(undefined4 **)(param_1 + 4);
      puVar5[1] = 0;
      uVar3 = DAT_00698abc;
      puVar5[2] = param_1;
      *puVar5 = uVar3;
      if (puVar5 != puVar7) {
        piVar8 = puVar5 + 1;
        DataMemoryBarrier(0xf);
        do {
          bVar1 = (bool)hasExclusiveAccess(piVar8);
        } while (!bVar1);
        *piVar8 = *piVar8 + 1;
        DataMemoryBarrier(0xf);
        piVar8 = *(int **)(param_1 + 4);
        *(undefined4 **)(param_1 + 4) = puVar5;
        if (piVar8 != (int *)0x0) {
          piVar9 = piVar8 + 1;
          DataMemoryBarrier(0xf);
          do {
            iVar6 = *piVar9;
            bVar1 = (bool)hasExclusiveAccess(piVar9);
          } while (!bVar1);
          *piVar9 = iVar6 + -1;
          DataMemoryBarrier(0xf);
          if (iVar6 + -1 == 0) {
            (**(code **)(*piVar8 + 4))(piVar8);
          }
          puVar5 = *(undefined4 **)(param_1 + 4);
        }
      }
      piVar4[2] = (int)puVar5;
      if (puVar5 != (undefined4 *)0x0) goto LAB_00698984;
    }
    else {
      piVar4[2] = (int)puVar5;
LAB_00698984:
      piVar8 = puVar5 + 1;
      DataMemoryBarrier(0xf);
      do {
        bVar1 = (bool)hasExclusiveAccess(piVar8);
      } while (!bVar1);
      *piVar8 = *piVar8 + 1;
      DataMemoryBarrier(0xf);
    }
    FUN_0062ab18(piVar4 + 3,param_2);
    iVar6 = DAT_00698ab8;
    piVar4[4] = iVar12;
    if (((*(int *)(iVar6 + 4) == 0) || (*(char *)(*(int *)(iVar6 + 4) + 4) != '\0')) ||
       (iVar12 = FUN_006986a0(piVar4), iVar12 == 0)) {
      piVar8 = piVar4 + 1;
      DataMemoryBarrier(0xf);
      do {
        bVar1 = (bool)hasExclusiveAccess(piVar8);
      } while (!bVar1);
      *piVar8 = *piVar8 + 1;
      DataMemoryBarrier(0xf);
      DataMemoryBarrier(0xf);
      do {
        iVar12 = *piVar8;
        bVar1 = (bool)hasExclusiveAccess(piVar8);
      } while (!bVar1);
      *piVar8 = iVar12 + -1;
      DataMemoryBarrier(0xf);
      if (iVar12 + -1 == 0) {
        (**(code **)(*piVar4 + 4))(piVar4);
      }
    }
    iVar11 = iVar11 + -4;
    iVar10 = iVar10 + -1;
  } while( true );
}

