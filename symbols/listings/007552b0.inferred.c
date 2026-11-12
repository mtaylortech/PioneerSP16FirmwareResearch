/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

/* WARNING: Unknown calling convention -- yet parameter storage is locked */
/* SUPPORTED ANALYST INTERPRETATION; address identity retained. Tail branch to 0069850c. Original
   source signature is not recovered. */

uint sp16_initialise_thunk_007552b0(LiveSamplerApplication_view_009327f0 *app)

{
  int iVar1;
  uint uVar2;
  pthread_t pVar3;
  int *piVar4;
  void *pvVar5;
  int *piVar6;
  code *pcVar7;
  undefined4 *puVar8;
  undefined1 auStack_20 [4];
  undefined1 auStack_1c [8];
  
  iVar1 = (**(code **)((int)app->primary_vtable + 0x10))();
  if ((iVar1 == 0) && (iVar1 = FUN_00696634(app), iVar1 != 0)) {
    uVar2 = 0;
  }
  else {
    pcVar7 = *(code **)((int)app->primary_vtable + 0x14);
    FUN_0069653c(auStack_20);
    (*pcVar7)(app,auStack_20);
    iVar1 = DAT_00698694;
    FUN_00627f38(auStack_20);
    app->initialise_wrapper_state = 0;
    puVar8 = *(undefined4 **)(iVar1 + 4);
    if (puVar8 == (undefined4 *)0x0) {
      puVar8 = operator_new(0x28);
      *puVar8 = 0;
      *(undefined1 *)(puVar8 + 1) = 0;
      *(undefined1 *)((int)puVar8 + 5) = 0;
      pVar3 = pthread_self();
      puVar8[3] = 0;
      puVar8[2] = pVar3;
      FUN_00644ca8(puVar8 + 4);
      if (*(int *)(iVar1 + 0x3c) != 0) {
        FUN_0064a3fc(auStack_1c,DAT_00698698);
        FUN_00646f6c(auStack_1c);
        FUN_00627f38(auStack_1c);
      }
      *(undefined4 **)(iVar1 + 4) = puVar8;
      juce_x11_queue_bootstrap_00697fc0();
      puVar8 = *(undefined4 **)(iVar1 + 4);
    }
    if (*(char *)(puVar8 + 1) == '\0') {
      pvVar5 = app->optional_listener;
      if (pvVar5 == (void *)0x0) {
        uVar2 = 1;
      }
      else {
        piVar6 = (int *)*puVar8;
        if (piVar6 == (int *)0x0) {
          piVar6 = operator_new(0x2c);
          iVar1 = DAT_0069869c;
          piVar6[1] = 0;
          piVar6[2] = 0;
          *piVar6 = iVar1;
          piVar6[3] = 0;
          piVar6[4] = 0;
          FUN_00644ca8(piVar6 + 5);
          piVar4 = (int *)*puVar8;
          if ((piVar6 != piVar4) && (*puVar8 = piVar6, piVar4 != (int *)0x0)) {
            (**(code **)(*piVar4 + 4))(piVar4,pvVar5);
            piVar6 = (int *)*puVar8;
          }
        }
        juce_register_listener_sorted_00696e68(piVar6,pvVar5);
        uVar2 = 1;
      }
    }
    else {
      uVar2 = 0;
    }
  }
  return uVar2;
}

