/* INFERRED PSEUDOCODE; names/types/indirect targets need instruction checks. No target execution. */

undefined4 FUN_00699a14(void)

{
  bool bVar1;
  int iVar2;
  int *piVar3;
  undefined4 *puVar4;
  pthread_t pVar5;
  int iVar6;
  int *piVar7;
  int iVar8;
  undefined1 auStack_14 [4];
  
  iVar2 = DAT_00699b58;
  if (*(int *)(DAT_00699b58 + 0x3c) != 0) {
    iVar8 = *(int *)(DAT_00699b58 + 4);
    if (iVar8 == 0) {
      puVar4 = operator_new(0x28);
      *puVar4 = 0;
      *(undefined1 *)(puVar4 + 1) = 0;
      *(undefined1 *)((int)puVar4 + 5) = 0;
      pVar5 = pthread_self();
      puVar4[3] = 0;
      puVar4[2] = pVar5;
      FUN_00644ca8(puVar4 + 4);
      if (*(int *)(iVar2 + 0x3c) != 0) {
        FUN_0064a3fc(auStack_14,DAT_00699b60);
        FUN_00646f6c(auStack_14);
        FUN_00627f38(auStack_14);
      }
      *(undefined4 **)(iVar2 + 4) = puVar4;
      FUN_00697fc0();
      iVar8 = *(int *)(iVar2 + 4);
    }
    piVar3 = operator_new(8);
    iVar6 = *(int *)(iVar2 + 4);
    piVar3[1] = 0;
    *piVar3 = DAT_00699b5c;
    if (((iVar6 == 0) || (*(char *)(iVar6 + 4) != '\0')) || (iVar6 = FUN_006986a0(), iVar6 == 0)) {
      piVar7 = piVar3 + 1;
      DataMemoryBarrier(0xf);
      do {
        bVar1 = (bool)hasExclusiveAccess(piVar7);
      } while (!bVar1);
      *piVar7 = *piVar7 + 1;
      DataMemoryBarrier(0xf);
      DataMemoryBarrier(0xf);
      do {
        iVar6 = *piVar7;
        bVar1 = (bool)hasExclusiveAccess(piVar7);
      } while (!bVar1);
      *piVar7 = iVar6 + -1;
      DataMemoryBarrier(0xf);
      if (iVar6 + -1 == 0) {
        (**(code **)(*piVar3 + 4))(piVar3);
      }
    }
    *(undefined1 *)(iVar8 + 4) = 1;
  }
  *(undefined1 *)(iVar2 + 0x60) = 1;
  return 0;
}

