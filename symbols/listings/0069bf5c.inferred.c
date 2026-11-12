/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_0069bf5c(int param_1,int param_2)

{
  bool bVar1;
  int iVar2;
  int iVar3;
  int iVar4;
  int *piVar5;
  int *piVar6;
  int *piVar7;
  int iVar8;
  undefined1 auStack_24 [8];
  
  iVar4 = DAT_0069c2d0;
  pthread_mutex_lock((pthread_mutex_t *)(DAT_0069c2d0 + 0x10));
  if (*(int *)(param_1 + 8) != 0) {
    iVar4 = *(int *)(iVar4 + 0xc);
    if (iVar4 == 0) goto LAB_0069bfdc;
    iVar3 = *(int *)(param_1 + 0x10);
    *(ulonglong *)(param_1 + 4) = CONCAT44(param_2,param_2);
    if ((iVar3 == 0) || (param_2 <= *(int *)(iVar3 + 4))) {
      iVar2 = *(int *)(param_1 + 0xc);
      if ((iVar2 == 0) || (*(int *)(iVar2 + 4) <= param_2)) goto LAB_0069bfdc;
LAB_0069c034:
      *(int *)(iVar2 + 0x10) = iVar3;
    }
    else {
      iVar2 = *(int *)(param_1 + 0xc);
      if (iVar2 != 0) goto LAB_0069c034;
      *(int *)(iVar4 + 0xe0) = iVar3;
    }
    if (*(int *)(param_1 + 0x10) != 0) {
      *(undefined4 *)(*(int *)(param_1 + 0x10) + 0xc) = *(undefined4 *)(param_1 + 0xc);
    }
    *(undefined4 *)(param_1 + 0x10) = 0;
    *(undefined4 *)(param_1 + 0xc) = 0;
    iVar3 = *(int *)(iVar4 + 0xe0);
    if ((iVar3 == 0) || (param_2 < *(int *)(iVar3 + 4))) {
      iVar3 = *(int *)(iVar4 + 0xe0);
      *(int *)(param_1 + 0x10) = iVar3;
      *(int *)(iVar4 + 0xe0) = param_1;
      if (iVar3 != 0) {
        *(int *)(iVar3 + 0xc) = param_1;
      }
      FUN_00637edc();
    }
    else {
      do {
        iVar4 = iVar3;
        iVar3 = *(int *)(iVar4 + 0x10);
        if (iVar3 == 0) break;
      } while (*(int *)(iVar3 + 4) <= param_2);
      *(int *)(param_1 + 0x10) = iVar3;
      *(int *)(iVar4 + 0x10) = param_1;
      *(int *)(param_1 + 0xc) = iVar4;
      if (*(int *)(param_1 + 0x10) != 0) {
        *(int *)(*(int *)(param_1 + 0x10) + 0xc) = param_1;
      }
      FUN_00637edc();
    }
    goto LAB_0069bfdc;
  }
  piVar7 = *(int **)(iVar4 + 0xc);
  iVar3 = param_2;
  if (param_2 < 1) {
    iVar3 = 1;
  }
  *(int *)(param_1 + 4) = param_2;
  *(int *)(param_1 + 8) = iVar3;
  if (piVar7 == (int *)0x0) {
    piVar7 = operator_new(0xe8);
    FUN_0064a3fc(auStack_24,DAT_0069c2d8);
    FUN_00637dc8(piVar7,auStack_24);
    FUN_00627f38(auStack_24);
    FUN_006967dc(piVar7 + 0x35);
    FUN_0069be8c(piVar7 + 0x36);
    iVar3 = DAT_0069c2dc;
    iVar8 = DAT_0069c2dc + 0x18;
    iVar2 = DAT_0069c2dc + 0x28;
    piVar5 = (int *)(piVar7[0x37] + 8);
    piVar7[0x38] = 0;
    piVar7[0x36] = iVar2;
    *piVar7 = iVar3;
    piVar7[0x35] = iVar8;
    piVar7[0x39] = 0;
    DataMemoryBarrier(0xf);
    do {
      iVar3 = *piVar5;
      if (iVar3 != 0) goto LAB_0069c1a4;
      bVar1 = (bool)hasExclusiveAccess(piVar5);
    } while (!bVar1);
    *piVar5 = 1;
    iVar3 = 0;
    DataMemoryBarrier(0xf);
LAB_0069c1a4:
    if (iVar3 == 0) {
      piVar5 = (int *)piVar7[0x37];
      if (((*(int *)(iVar4 + 4) == 0) || (*(char *)(*(int *)(iVar4 + 4) + 4) != '\0')) ||
         (iVar3 = FUN_006986a0(piVar5), iVar3 == 0)) {
        if (piVar5 != (int *)0x0) {
          piVar6 = piVar5 + 1;
          DataMemoryBarrier(0xf);
          do {
            bVar1 = (bool)hasExclusiveAccess(piVar6);
          } while (!bVar1);
          *piVar6 = *piVar6 + 1;
          DataMemoryBarrier(0xf);
          DataMemoryBarrier(0xf);
          do {
            iVar3 = *piVar6;
            bVar1 = (bool)hasExclusiveAccess(piVar6);
          } while (!bVar1);
          *piVar6 = iVar3 + -1;
          DataMemoryBarrier(0xf);
          if (iVar3 + -1 == 0) {
            (**(code **)(*piVar5 + 4))(piVar5);
          }
        }
        piVar5 = (int *)(piVar7[0x37] + 8);
        iVar3 = *(int *)(piVar7[0x37] + 8);
        do {
          DataMemoryBarrier(0xf);
          do {
            iVar2 = *piVar5;
            if (*piVar5 != iVar3) goto LAB_0069c27c;
            bVar1 = (bool)hasExclusiveAccess(piVar5);
          } while (!bVar1);
          *piVar5 = 0;
          DataMemoryBarrier(0xf);
          iVar2 = iVar3;
LAB_0069c27c:
          if (iVar2 == iVar3) goto code_r0x0069c284;
          iVar3 = *piVar5;
        } while( true );
      }
      *(int **)(iVar4 + 0xc) = piVar7;
    }
    else {
      *(int **)(iVar4 + 0xc) = piVar7;
    }
    goto LAB_0069c1b0;
  }
  iVar4 = piVar7[0x38];
  goto joined_r0x0069c1b8;
code_r0x0069c284:
  *(int **)(iVar4 + 0xc) = piVar7;
LAB_0069c1b0:
  iVar4 = piVar7[0x38];
joined_r0x0069c1b8:
  if ((iVar4 == 0) || (*(int *)(param_1 + 4) < *(int *)(iVar4 + 4))) {
    iVar4 = piVar7[0x38];
    *(int *)(param_1 + 0x10) = iVar4;
    piVar7[0x38] = param_1;
  }
  else {
    do {
      iVar3 = iVar4;
      iVar4 = *(int *)(iVar3 + 0x10);
      if (iVar4 == 0) break;
    } while (*(int *)(iVar4 + 4) <= *(int *)(param_1 + 4));
    *(int *)(param_1 + 0x10) = iVar4;
    *(int *)(param_1 + 0xc) = iVar3;
    *(int *)(iVar3 + 0x10) = param_1;
    iVar4 = *(int *)(param_1 + 0x10);
  }
  if (iVar4 != 0) {
    *(int *)(iVar4 + 0xc) = param_1;
  }
  FUN_00637edc(piVar7);
LAB_0069bfdc:
  pthread_mutex_unlock(DAT_0069c2d4);
  return;
}

