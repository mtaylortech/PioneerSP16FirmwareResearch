/* INFERRED PSEUDOCODE; names/types/indirect targets need instruction checks. No target execution. */

undefined4 FUN_00698468(undefined4 param_1)

{
  int iVar1;
  undefined4 *puVar2;
  pthread_t pVar3;
  int iVar4;
  undefined1 auStack_1c [8];
  
  iVar1 = DAT_00698504;
  iVar4 = *(int *)(DAT_00698504 + 0x5c);
  *(int *)(DAT_00698504 + 0x5c) = iVar4 + 1;
  if ((iVar4 == 0) && (*(int *)(iVar1 + 4) == 0)) {
    puVar2 = operator_new(0x28);
    *puVar2 = 0;
    *(undefined1 *)(puVar2 + 1) = 0;
    *(undefined1 *)((int)puVar2 + 5) = 0;
    pVar3 = pthread_self();
    puVar2[3] = 0;
    puVar2[2] = pVar3;
    FUN_00644ca8(puVar2 + 4);
    if (*(int *)(iVar1 + 0x3c) != 0) {
      FUN_0064a3fc(auStack_1c,DAT_00698508);
      FUN_00646f6c(auStack_1c);
      FUN_00627f38(auStack_1c);
    }
    *(undefined4 **)(iVar1 + 4) = puVar2;
    FUN_00697fc0();
  }
  return param_1;
}

