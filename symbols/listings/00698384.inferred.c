/* INFERRED PSEUDOCODE; names/types/indirect targets need instruction checks. No target execution. */

int FUN_00698384(int *param_1)

{
  undefined4 *puVar1;
  pthread_t pVar2;
  int iVar3;
  int iVar4;
  int *piVar5;
  undefined1 auStack_1c [8];
  
  iVar4 = DAT_00698460;
  iVar3 = param_1[3];
  if (iVar3 != 0) {
    piVar5 = *(int **)(DAT_00698460 + 4);
    if (piVar5 == (int *)0x0) {
      puVar1 = operator_new(0x28);
      *puVar1 = 0;
      *(undefined1 *)(puVar1 + 1) = 0;
      *(undefined1 *)((int)puVar1 + 5) = 0;
      pVar2 = pthread_self();
      puVar1[3] = 0;
      puVar1[2] = pVar2;
      FUN_00644ca8(puVar1 + 4);
      if (*(int *)(iVar4 + 0x3c) != 0) {
        FUN_0064a3fc(auStack_1c,DAT_00698464);
        FUN_00646f6c(auStack_1c);
        FUN_00627f38(auStack_1c);
      }
      *(undefined4 **)(iVar4 + 4) = puVar1;
      FUN_00697fc0();
      iVar3 = param_1[3];
      piVar5 = *(int **)(iVar4 + 4);
    }
    if (*piVar5 != 0) {
      FUN_00697074(*piVar5,iVar3);
    }
  }
  (**(code **)(*param_1 + 0x18))(param_1);
  if ((int *)param_1[3] != (int *)0x0) {
    iVar4 = *(int *)param_1[3];
    param_1[3] = 0;
    (**(code **)(iVar4 + 4))();
  }
  return param_1[1];
}

