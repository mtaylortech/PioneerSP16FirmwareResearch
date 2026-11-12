/* INFERRED PSEUDOCODE; names/types/indirect targets need instruction checks. No target execution. */

void FUN_00699728(void)

{
  bool bVar1;
  int *piVar2;
  undefined4 *puVar3;
  pthread_t pVar4;
  int iVar5;
  int *piVar6;
  int iVar7;
  undefined1 auStack_14 [4];
  
  iVar5 = DAT_00699854;
  iVar7 = *(int *)(DAT_00699854 + 4);
  if (iVar7 == 0) {
    puVar3 = operator_new(0x28);
    *puVar3 = 0;
    *(undefined1 *)(puVar3 + 1) = 0;
    *(undefined1 *)((int)puVar3 + 5) = 0;
    pVar4 = pthread_self();
    puVar3[3] = 0;
    puVar3[2] = pVar4;
    FUN_00644ca8(puVar3 + 4);
    if (*(int *)(iVar5 + 0x3c) != 0) {
      FUN_0064a3fc(auStack_14,DAT_0069985c);
      FUN_00646f6c(auStack_14);
      FUN_00627f38(auStack_14);
    }
    *(undefined4 **)(iVar5 + 4) = puVar3;
    FUN_00697fc0();
    iVar7 = *(int *)(iVar5 + 4);
  }
  piVar2 = operator_new(8);
  iVar5 = *(int *)(iVar5 + 4);
  piVar2[1] = 0;
  *piVar2 = DAT_00699858;
  if (((iVar5 == 0) || (*(char *)(iVar5 + 4) != '\0')) || (iVar5 = FUN_006986a0(), iVar5 == 0)) {
    piVar6 = piVar2 + 1;
    DataMemoryBarrier(0xf);
    do {
      bVar1 = (bool)hasExclusiveAccess(piVar6);
    } while (!bVar1);
    *piVar6 = *piVar6 + 1;
    DataMemoryBarrier(0xf);
    DataMemoryBarrier(0xf);
    do {
      iVar5 = *piVar6;
      bVar1 = (bool)hasExclusiveAccess(piVar6);
    } while (!bVar1);
    *piVar6 = iVar5 + -1;
    DataMemoryBarrier(0xf);
    if (iVar5 + -1 == 0) {
      (**(code **)(*piVar2 + 4))(piVar2);
    }
  }
  *(undefined1 *)(iVar7 + 4) = 1;
  return;
}

