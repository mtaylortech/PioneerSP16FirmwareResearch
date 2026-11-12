/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

/* WARNING: Unknown calling convention -- yet parameter storage is locked */
/* SUPPORTED ANALYST INTERPRETATION; address identity retained. Constructs settings, UIThread, mode
   graph and MainWindow. Normal return 0057222c; caller ignores r0, so void is a working convention.
   Original source signature is not recovered. */

void sp16_initialise_00571d24(LiveSamplerApplication_view_009327f0 *app,void *startup_context)

{
  char *pcVar1;
  undefined1 *puVar2;
  byte bVar3;
  void *pvVar4;
  undefined4 uVar5;
  int *piVar6;
  uint uVar7;
  uint uVar8;
  uint uVar9;
  uint uVar10;
  uint uVar11;
  uint uVar12;
  void *pvVar13;
  int *piVar14;
  int *piVar15;
  undefined4 *puVar16;
  int iVar17;
  statvfs local_b4;
  undefined1 auStack_6c [12];
  undefined1 local_60;
  undefined1 local_5f;
  undefined1 local_5e;
  undefined1 local_5d;
  undefined1 auStack_5c [4];
  undefined1 auStack_58 [4];
  undefined1 auStack_54 [4];
  undefined1 auStack_50 [4];
  undefined1 auStack_4c [4];
  undefined1 auStack_48 [4];
  undefined1 auStack_44 [4];
  undefined1 auStack_40 [4];
  undefined1 auStack_3c [4];
  undefined1 auStack_38 [4];
  undefined1 auStack_34 [4];
  undefined1 auStack_30 [4];
  byte local_2c;
  
  if (((*DAT_005727a8 & 1) == 0) && (iVar17 = __cxa_guard_acquire(DAT_005727a8), iVar17 != 0)) {
    FUN_0064a3fc(DAT_005727b4,DAT_00572800);
    FUN_0064a3fc(DAT_00572804,DAT_00572808);
    FUN_0064a3fc(DAT_0057280c,DAT_00572810);
    FUN_0064a3fc(DAT_00572814,DAT_00572818);
    __cxa_guard_release(DAT_005727a8);
    __aeabi_atexit(0,DAT_0057281c,DAT_005727fc);
  }
  if (((*DAT_005727ac & 1) == 0) && (iVar17 = __cxa_guard_acquire(), iVar17 != 0)) {
    puVar16 = DAT_005727b0 + 1;
    *DAT_005727b0 = 0x5e715e28;
    FUN_006370b0(puVar16,1);
    FUN_006370b0(DAT_005727f4,1);
    __cxa_guard_release(DAT_005727ac);
    __aeabi_atexit(DAT_005727b0,DAT_005727f8,DAT_005727fc);
  }
  TSP16VirtualPathSetting_renameToraiz_0037c428(DAT_005727b4,DAT_005727b0);
  pvVar4 = operator_new(0x330);
  Settings_construct_0056c4bc(pvVar4,DAT_005727b8,DAT_005727bc);
  DAT_00f6dbf8 = (undefined4 *)&app->field_0x44;
  app->settings = pvVar4;
  local_5f = 0;
  local_5e = 0;
  local_5d = 0;
  local_60 = 1;
  FUN_0050a6e8(&local_60);
  FUN_00636894(auStack_54,startup_context);
  FUN_00636880(auStack_50,DAT_005727c0);
  FUN_00636880(auStack_4c,DAT_005727c4);
  sp16_mode_tokens_construct_0065e09c(auStack_6c,auStack_54,auStack_50,auStack_4c);
  if (DAT_00f6e380 == (void *)0x0) {
    pthread_mutex_lock(DAT_00572824);
    puVar2 = DAT_00572848;
    pcVar1 = DAT_00572844;
    if ((DAT_00f6e380 == (void *)0x0) && (*DAT_00572844 == '\0')) {
      *DAT_00572844 = '\x01';
      *puVar2 = 1;
      pvVar4 = operator_new(0xc);
      FUN_00556044();
      *pcVar1 = '\0';
      DAT_00f6e380 = pvVar4;
    }
    pthread_mutex_unlock(DAT_00572824);
  }
  pvVar4 = DAT_00f6e380;
  FUN_00636880(auStack_5c,DAT_005727c8);
  uVar5 = FUN_00636d20(auStack_6c,auStack_5c,0);
  sp16_device_initialise_0055659c(pvVar4,uVar5);
  pvVar4 = operator_new(0x418);
  UIThread_construct_0056cd14(pvVar4);
  app->ui_thread = pvVar4;
  if (DAT_00f6e380 == (void *)0x0) {
    pthread_mutex_lock(DAT_00572824);
    puVar2 = DAT_00572848;
    pcVar1 = DAT_00572844;
    if ((*DAT_00572828 == 0) && (*DAT_00572844 == '\0')) {
      *DAT_00572844 = '\x01';
      *puVar2 = 1;
      pvVar13 = operator_new(0xc);
      FUN_00556044();
      DAT_00f6e380 = pvVar13;
      *pcVar1 = '\0';
    }
    pthread_mutex_unlock(DAT_00572824);
  }
  FUN_0056e28c(pvVar4,DAT_00f6e380);
  piVar6 = DAT_005727cc;
  pvVar4 = app->ui_thread;
  iVar17 = *DAT_005727cc;
  if (iVar17 == 0) {
    pthread_mutex_lock(DAT_00572830);
    puVar2 = DAT_00572840;
    pcVar1 = DAT_0057283c;
    if ((*piVar6 == 0) && (*DAT_0057283c == '\0')) {
      *DAT_0057283c = '\x01';
      *puVar2 = 1;
      pvVar13 = operator_new(0x3f0);
      FUN_00562370();
      *piVar6 = (int)pvVar13;
      *pcVar1 = '\0';
    }
    pthread_mutex_unlock(DAT_00572830);
    iVar17 = *piVar6;
  }
  FUN_0056e2e4(pvVar4,iVar17);
  UIThread_start_0056cfe4(app->ui_thread);
  sleep_milliseconds_006457dc(0x1e);
  if (DAT_00f6e380 == (void *)0x0) {
    pthread_mutex_lock(DAT_00572824);
    puVar2 = DAT_00572848;
    pcVar1 = DAT_00572844;
    if ((*DAT_00572828 == 0) && (*DAT_00572844 == '\0')) {
      *DAT_00572844 = '\x01';
      *puVar2 = 1;
      pvVar4 = operator_new(0xc);
      FUN_00556044();
      *pcVar1 = '\0';
      DAT_00f6e380 = pvVar4;
    }
    pthread_mutex_unlock(DAT_00572824);
  }
  pvVar4 = DAT_00f6e380;
  iVar17 = 0x1e;
  do {
    piVar6 = (int *)FUN_005560bc(pvVar4,10);
    uVar7 = (**(code **)(*piVar6 + 0xc))();
    piVar6 = (int *)FUN_005560bc(pvVar4,2);
    uVar8 = (**(code **)(*piVar6 + 0xc))();
    piVar6 = (int *)FUN_005560bc(pvVar4,0x15);
    uVar9 = (**(code **)(*piVar6 + 0xc))();
    piVar6 = (int *)FUN_005560bc(pvVar4,3);
    uVar10 = (**(code **)(*piVar6 + 0xc))();
    piVar6 = (int *)FUN_005560bc(pvVar4,4);
    uVar11 = (**(code **)(*piVar6 + 0xc))();
    piVar6 = (int *)FUN_005560bc(pvVar4,5);
    uVar12 = (**(code **)(*piVar6 + 0xc))();
    if ((uVar8 & uVar7 & uVar9) != 0) break;
    if ((uVar11 & uVar10 & uVar12) != 0) {
      FUN_0064a3fc(auStack_34,DAT_005727d4);
      FUN_006573dc(auStack_6c,auStack_34,0);
      FUN_00627f38(auStack_34);
      break;
    }
    sleep_milliseconds_006457dc(1);
    iVar17 = iVar17 + -1;
  } while (iVar17 != 0);
  local_2c = 0;
  FUN_00636880(auStack_48,DAT_005727c8);
  bVar3 = FUN_00636d20(auStack_6c,auStack_48,0);
  local_2c = local_2c & 0xfe | bVar3 & 1;
  FUN_00636880(auStack_44,DAT_005727d0);
  bVar3 = FUN_00636d20(auStack_6c,auStack_44,0);
  local_2c = local_2c & 0xfd | (bVar3 & 1) << 1;
  FUN_00636880(auStack_40,DAT_005727d4);
  bVar3 = FUN_00636d20(auStack_6c,auStack_40,0);
  local_2c = local_2c & 0xfb | (bVar3 & 1) << 2;
  FUN_00636880(auStack_3c,DAT_005727d8);
  bVar3 = FUN_00636d20(auStack_6c,auStack_3c,0);
  local_2c = local_2c & 0xf7 | (bVar3 & 1) << 3;
  FUN_00636880(auStack_38,DAT_005727dc);
  uVar7 = FUN_00636d20(auStack_6c,auStack_38,0);
  uVar8 = (uint)local_2c;
  uVar7 = (uVar7 & 1) << 4;
  local_2c = (byte)(uVar8 & 0xffffffef) | (byte)uVar7;
  uVar7 = uVar8 & 0xffffffef | uVar7;
  sp16_build_mode_graph_005712cc(app,uVar7);
  sp16_wire_graph_controllers_0057155c(app,uVar7);
  pvVar13 = sp16_create_mode_content_0056f7f4(app,uVar7);
  (**(code **)((int)app->primary_vtable + 8))(auStack_58,app);
  piVar6 = operator_new(0x108);
  FUN_006c1630(auStack_30,DAT_005727e0);
  FUN_007da7d8(piVar6,auStack_58,auStack_30,7,1);
  FUN_006a0280(auStack_30);
  pvVar4 = DAT_00f6e380;
  piVar6[0x40] = 0;
  *piVar6 = DAT_005727e4;
  if (pvVar4 == (void *)0x0) {
    pthread_mutex_lock(DAT_00572824);
    puVar2 = DAT_00572848;
    pcVar1 = DAT_00572844;
    if ((*DAT_00572828 == 0) && (*DAT_00572844 == '\0')) {
      *DAT_00572844 = '\x01';
      *puVar2 = 1;
      pvVar4 = operator_new(0xc);
      FUN_00556044();
      *pcVar1 = '\0';
      DAT_00f6e380 = pvVar4;
    }
    pthread_mutex_unlock(DAT_00572824);
    pvVar4 = DAT_00f6e380;
  }
  piVar14 = operator_new(0x48);
  FUN_004f70c4(piVar14,pvVar4);
  piVar15 = (int *)piVar6[0x40];
  if ((piVar14 != piVar15) && (piVar6[0x40] = (int)piVar14, piVar15 != (int *)0x0)) {
    (**(code **)(*piVar15 + 4))();
  }
  FUN_0079be58(pvVar13,0,0,800,0x1e0);
  FUN_00780c78(piVar6,0,0);
  FUN_0079a10c(piVar6,0);
  FUN_007d0734(piVar6,pvVar13,1);
  FUN_0079c7e0(piVar6,piVar6[6],piVar6[7]);
  FUN_0079b524(piVar6,1);
  piVar14 = app->main_window;
  if ((piVar6 != piVar14) && (app->main_window = piVar6, piVar14 != (int *)0x0)) {
    (**(code **)(*piVar14 + 4))();
  }
  FUN_00627f38(auStack_58);
  if (app->processing_graph != (int *)0x0) {
    (**(code **)(*(int *)app->processing_graph + 200))();
  }
  piVar6 = DAT_005727e8;
  iVar17 = *DAT_005727e8;
  if (iVar17 == 0) {
    pthread_mutex_lock(DAT_0057282c);
    pcVar1 = DAT_0057284c;
    if (((*piVar6 == 0) && (*DAT_0057284c == '\0')) && (*DAT_00572850 == '\0')) {
      *DAT_00572850 = '\x01';
      *pcVar1 = '\x01';
      pvVar4 = operator_new(0x170);
      FUN_0037fba8();
      *piVar6 = (int)pvVar4;
      *pcVar1 = '\0';
    }
    pthread_mutex_unlock(DAT_0057282c);
    iVar17 = *piVar6;
  }
  FUN_0037fd38(iVar17);
  piVar6 = DAT_005727ec;
  iVar17 = *DAT_005727ec;
  if (iVar17 == 0) {
    pthread_mutex_lock(DAT_00572820);
    pcVar1 = DAT_00572834;
    if (((*piVar6 == 0) && (*DAT_00572834 == '\0')) && (*DAT_00572838 == '\0')) {
      *DAT_00572838 = '\x01';
      *pcVar1 = '\x01';
      pvVar4 = operator_new(0x8c0);
      FUN_00522aa0();
      *piVar6 = (int)pvVar4;
      *pcVar1 = '\0';
    }
    pthread_mutex_unlock(DAT_00572820);
    iVar17 = *piVar6;
  }
  FUN_00523514(iVar17);
  statvfs(DAT_005727f0,&local_b4);
  if ((int)((uint)((ulonglong)local_b4.f_bsize * (ulonglong)local_b4.f_bfree) >> 0x14 |
           (int)((ulonglong)local_b4.f_bsize * (ulonglong)local_b4.f_bfree >> 0x20) << 0xc) < 10) {
    (**(code **)*DAT_00f6dbf8)(DAT_00f6dbf8,0xe,0);
  }
  FUN_00653de0(auStack_6c);
  return;
}

