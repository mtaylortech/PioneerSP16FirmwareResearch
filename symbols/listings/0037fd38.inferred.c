/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_0037fd38(int param_1,undefined4 param_2,undefined4 param_3,undefined4 param_4)

{
  int *piVar1;
  int *piVar2;
  char *pcVar3;
  undefined1 *puVar4;
  void *pvVar5;
  int iVar6;
  
  piVar1 = DAT_0037ffb8;
  if (*DAT_0037ffb8 == 0) {
    pthread_mutex_lock(DAT_0037ffc4);
    puVar4 = DAT_0037ffd4;
    pcVar3 = DAT_0037ffd0;
    if ((*piVar1 == 0) && (*DAT_0037ffd0 == '\0')) {
      *DAT_0037ffd0 = '\x01';
      *puVar4 = 1;
      pvVar5 = operator_new(0xe8);
      FUN_00383484();
      *piVar1 = (int)pvVar5;
      *pcVar3 = '\0';
    }
    pthread_mutex_unlock(DAT_0037ffc4);
    FUN_003835b4(*piVar1,param_1 + 0xc);
    pvVar5 = (void *)*piVar1;
    piVar2 = DAT_0037ffbc;
  }
  else {
    FUN_003835b4(*DAT_0037ffb8,param_1 + 0xc,param_3,param_4,param_4);
    pvVar5 = (void *)*piVar1;
    piVar2 = DAT_0037ffbc;
  }
  DAT_0037ffbc = piVar2;
  if (pvVar5 == (void *)0x0) {
    pthread_mutex_lock(DAT_0037ffc4);
    puVar4 = DAT_0037ffd4;
    pcVar3 = DAT_0037ffd0;
    if ((*DAT_0037ffb8 == 0) && (*DAT_0037ffd0 == '\0')) {
      *DAT_0037ffd0 = '\x01';
      *puVar4 = 1;
      pvVar5 = operator_new(0xe8);
      FUN_00383484();
      *piVar1 = (int)pvVar5;
      *pcVar3 = '\0';
    }
    pthread_mutex_unlock(DAT_0037ffc4);
    piVar2 = DAT_0037ffbc;
    juce_start_thread_0064703c((void *)*piVar1);
    pvVar5 = (void *)*piVar2;
    piVar1 = DAT_0037ffc0;
  }
  else {
    juce_start_thread_0064703c(pvVar5);
    pvVar5 = (void *)*piVar2;
    piVar1 = DAT_0037ffc0;
  }
  DAT_0037ffc0 = piVar1;
  if (pvVar5 == (void *)0x0) {
    pthread_mutex_lock(DAT_0037ffc8);
    puVar4 = DAT_0037ffe4;
    pcVar3 = DAT_0037ffe0;
    if ((*piVar2 == 0) && (*DAT_0037ffe0 == '\0')) {
      *DAT_0037ffe0 = '\x01';
      *puVar4 = 1;
      pvVar5 = operator_new(0x100);
      FUN_0037ee58();
      *piVar2 = (int)pvVar5;
      *pcVar3 = '\0';
    }
    pthread_mutex_unlock(DAT_0037ffc8);
    piVar1 = DAT_0037ffc0;
    juce_start_thread_0064703c((void *)*piVar2);
    iVar6 = *piVar1;
  }
  else {
    juce_start_thread_0064703c(pvVar5);
    iVar6 = *piVar1;
  }
  if (iVar6 == 0) {
    pthread_mutex_lock(DAT_0037ffcc);
    puVar4 = DAT_0037ffdc;
    pcVar3 = DAT_0037ffd8;
    if ((*piVar1 == 0) && (*DAT_0037ffd8 == '\0')) {
      *DAT_0037ffd8 = '\x01';
      *puVar4 = 1;
      pvVar5 = operator_new(0x34);
      FUN_0037df74();
      *piVar1 = (int)pvVar5;
      *pcVar3 = '\0';
    }
    pthread_mutex_unlock(DAT_0037ffcc);
    iVar6 = *piVar1;
  }
  FUN_0037d1f0(iVar6,4,param_1 + 0x10);
  juce_start_thread_0064703c((void *)(param_1 + 0x50));
  return;
}

