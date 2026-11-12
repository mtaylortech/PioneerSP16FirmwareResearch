/* INFERRED PSEUDOCODE; names/types/indirect targets need instruction checks. No target execution. */

void FUN_006982fc(void)

{
  int iVar1;
  undefined4 *puVar2;
  pthread_t pVar3;
  undefined1 auStack_14 [4];
  
  iVar1 = DAT_0069837c;
  if (*(int *)(DAT_0069837c + 4) == 0) {
    puVar2 = operator_new(0x28);
    *puVar2 = 0;
    *(undefined1 *)(puVar2 + 1) = 0;
    *(undefined1 *)((int)puVar2 + 5) = 0;
    pVar3 = pthread_self();
    puVar2[3] = 0;
    puVar2[2] = pVar3;
    FUN_00644ca8(puVar2 + 4);
    if (*(int *)(iVar1 + 0x3c) != 0) {
      FUN_0064a3fc(auStack_14,DAT_00698380);
      FUN_00646f6c(auStack_14);
      FUN_00627f38(auStack_14);
    }
    *(undefined4 **)(iVar1 + 4) = puVar2;
    FUN_00697fc0();
  }
  return;
}

