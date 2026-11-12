/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_004f644c(int param_1,int param_2,int *param_3)

{
  bool bVar1;
  pthread_t pVar2;
  int iVar3;
  int *piVar4;
  int *piVar5;
  int iVar6;
  pthread_t pVar7;
  int iVar8;
  
  pVar2 = pthread_self();
  iVar3 = FUN_00696cf4();
  if (iVar3 == 0) {
    pVar7 = 0;
  }
  else {
    pVar7 = *(pthread_t *)(iVar3 + 8);
  }
  if (pVar2 == pVar7) {
    iVar3 = param_3[1];
    *(int *)(param_1 + 0x38) = *param_3;
    *(int *)(param_1 + 0x3c) = iVar3;
    return;
  }
  iVar8 = *param_3;
  iVar3 = param_3[1];
  piVar4 = operator_new(0x28);
  piVar5 = DAT_004f65e4;
  *piVar4 = DAT_004f65e0;
  piVar4[9] = 0x5e715e28;
  DataMemoryBarrier(0xf);
  do {
    iVar6 = *piVar5;
    bVar1 = (bool)hasExclusiveAccess(piVar5);
  } while (!bVar1);
  *piVar5 = iVar6 + 1;
  DataMemoryBarrier(0xf);
  piVar4[1] = iVar6 + 1;
  FUN_00696c6c(piVar4 + 2);
  iVar6 = DAT_004f65e8;
  piVar4[8] = param_2;
  *(undefined1 *)(piVar4 + 4) = 0;
  *piVar4 = iVar6 + 0x40;
  piVar4[2] = iVar6 + 0x58;
  piVar4[5] = param_1;
  piVar4[6] = iVar8;
  piVar4[7] = iVar3;
  pVar2 = pthread_self();
  pVar7 = (**(code **)(*(int *)(param_1 + 0x18) + 8))(param_1 + 0x18);
  if (pVar2 == pVar7) {
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
  FUN_004f782c(DAT_004f65ec,DAT_004f65f0,DAT_004f65f4);
  *(undefined4 *)(param_1 + 0x20) = 0;
  return;
}

