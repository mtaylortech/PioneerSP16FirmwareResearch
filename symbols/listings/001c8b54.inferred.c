/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_001c8b54(int param_1,int param_2,int param_3)

{
  bool bVar1;
  pthread_t pVar2;
  pthread_t pVar3;
  int *piVar4;
  int *piVar5;
  int iVar6;
  undefined1 *puVar7;
  int *piVar8;
  
  pVar2 = pthread_self();
  pVar3 = (**(code **)(**(int **)(param_1 + 0xb4) + 8))();
  if (pVar2 == pVar3) {
    puVar7 = *(undefined1 **)(param_1 + 0x124);
    iVar6 = *(int *)(puVar7 + 0x1c);
    if ((*(int *)(puVar7 + 0x1c) <= param_2) &&
       (iVar6 = param_2, *(int *)(puVar7 + 0x20) <= param_2)) {
      iVar6 = *(int *)(puVar7 + 0x20);
    }
    *(int *)(puVar7 + 4) = iVar6;
    *(int *)(puVar7 + 0x10) = param_3;
    *puVar7 = 0;
    return;
  }
  piVar8 = *(int **)(param_1 + 0xb4);
  piVar4 = operator_new(0x24);
  piVar5 = DAT_001c8d04;
  iVar6 = DAT_001c8d00;
  piVar4[8] = 0x5e715e28;
  *piVar4 = iVar6;
  DataMemoryBarrier(0xf);
  do {
    iVar6 = *piVar5;
    bVar1 = (bool)hasExclusiveAccess(piVar5);
  } while (!bVar1);
  *piVar5 = iVar6 + 1;
  DataMemoryBarrier(0xf);
  piVar4[1] = iVar6 + 1;
  FUN_00696c6c(piVar4 + 2);
  iVar6 = DAT_001c8d08;
  piVar4[5] = param_1;
  *(undefined1 *)(piVar4 + 4) = 0;
  *piVar4 = iVar6 + 0x40;
  piVar4[2] = iVar6 + 0x58;
  piVar4[6] = param_3;
  piVar4[7] = param_2;
  pVar2 = pthread_self();
  pVar3 = (**(code **)(*piVar8 + 8))(piVar8);
  if (pVar2 == pVar3) {
    if (((char)piVar4[4] == '\0') || (piVar4[1] != 0)) {
      (**(code **)(*piVar4 + 8))(piVar4);
    }
    (**(code **)(*piVar4 + 4))(piVar4);
    return;
  }
  iVar6 = (**(code **)(*piVar8 + 0x10))(piVar8,piVar4,0);
  if (iVar6 == 0) {
    return;
  }
  piVar5 = (int *)piVar8[2];
  if (piVar5 != (int *)0x0) {
    if ((((uint)piVar5 & 3) == 0) && (piVar5[1] == 0x5e715e28)) {
      (**(code **)(*piVar5 + 8))();
      return;
    }
    FUN_004f782c(DAT_001c8d0c,DAT_001c8d10,DAT_001c8d14);
    piVar8[2] = 0;
    return;
  }
  return;
}

