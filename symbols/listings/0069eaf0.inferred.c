/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void candidate_0069eaf0(void)

{
  bool bVar1;
  int iVar2;
  int *piVar3;
  int iVar4;
  int iVar5;
  int iVar6;
  
  iVar6 = *(int *)(_UNK_0069ec88 + 0xc);
  if (iVar6 == 0) {
    return;
  }
  pthread_mutex_lock((pthread_mutex_t *)(_UNK_0069ec88 + 0x10));
  if ((*(int *)(iVar6 + 0xe0) != 0) && (*(int *)(*(int *)(iVar6 + 0xe0) + 4) < 1)) {
    piVar3 = *(int **)(iVar6 + 0xe0);
    iVar4 = piVar3[3];
    iVar2 = piVar3[2];
    piVar3[1] = iVar2;
    if (iVar4 == 0) goto LAB_0069ec38;
LAB_0069eb90:
    *(int *)(iVar4 + 0x10) = piVar3[4];
    do {
      if (piVar3[4] != 0) {
        *(int *)(piVar3[4] + 0xc) = piVar3[3];
      }
      piVar3[4] = 0;
      piVar3[3] = 0;
      iVar4 = *(int *)(iVar6 + 0xe0);
      if ((iVar4 == 0) || (iVar2 < *(int *)(iVar4 + 4))) {
        iVar2 = *(int *)(iVar6 + 0xe0);
        piVar3[4] = iVar2;
        *(int **)(iVar6 + 0xe0) = piVar3;
      }
      else {
        do {
          iVar5 = iVar4;
          iVar4 = *(int *)(iVar5 + 0x10);
          if (iVar4 == 0) break;
        } while (*(int *)(iVar4 + 4) <= iVar2);
        piVar3[4] = iVar4;
        piVar3[3] = iVar5;
        *(int **)(iVar5 + 0x10) = piVar3;
        iVar2 = piVar3[4];
      }
      if (iVar2 != 0) {
        *(int **)(iVar2 + 0xc) = piVar3;
      }
      FUN_00637edc(iVar6);
      pthread_mutex_unlock(_UNK_0069ec8c);
      (**(code **)(*piVar3 + 8))(piVar3);
      pthread_mutex_lock(_UNK_0069ec8c);
      if ((*(int *)(iVar6 + 0xe0) == 0) || (0 < *(int *)(*(int *)(iVar6 + 0xe0) + 4))) break;
      piVar3 = *(int **)(iVar6 + 0xe0);
      iVar4 = piVar3[3];
      iVar2 = piVar3[2];
      piVar3[1] = iVar2;
      if (iVar4 != 0) goto LAB_0069eb90;
LAB_0069ec38:
      *(int *)(iVar6 + 0xe0) = piVar3[4];
    } while( true );
  }
  piVar3 = (int *)(iVar6 + 0xe4);
  iVar6 = *(int *)(iVar6 + 0xe4);
  do {
    DataMemoryBarrier(0xf);
    do {
      iVar2 = *piVar3;
      if (*piVar3 != iVar6) goto LAB_0069eb60;
      bVar1 = (bool)hasExclusiveAccess(piVar3);
    } while (!bVar1);
    *piVar3 = 0;
    DataMemoryBarrier(0xf);
    iVar2 = iVar6;
LAB_0069eb60:
    if (iVar2 == iVar6) {
      (*(code *)PTR_pthread_mutex_unlock_00b70d88)(_UNK_0069ec8c);
      return;
    }
    iVar6 = *piVar3;
  } while( true );
}

