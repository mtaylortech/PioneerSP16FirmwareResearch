/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

/* SUPPORTED ANALYST INTERPRETATION; address identity retained. Original full method diagnostic
   string survives. Original source signature is not recovered. */

void TSP16VirtualPathSetting_renameToraiz_0037c428(undefined4 param_1,int param_2)

{
  uint *puVar1;
  int iVar2;
  undefined4 uVar3;
  undefined4 *puVar4;
  undefined1 auStack_58 [8];
  undefined1 auStack_50 [4];
  undefined1 auStack_4c [4];
  undefined1 auStack_48 [4];
  undefined1 auStack_44 [4];
  undefined1 auStack_40 [4];
  undefined1 auStack_3c [4];
  undefined1 auStack_38 [4];
  undefined1 auStack_34 [4];
  undefined1 auStack_30 [4];
  undefined1 auStack_2c [4];
  undefined1 auStack_28 [4];
  undefined1 auStack_24 [4];
  undefined1 auStack_20 [4];
  undefined1 auStack_1c [4];
  undefined1 auStack_18 [4];
  undefined1 auStack_14 [4];
  
  puVar1 = DAT_0037ca7c;
  if (*DAT_0037ca78 != '\0') {
    *DAT_0037ca78 = '\0';
    if (((*puVar1 & 1) == 0) && (iVar2 = __cxa_guard_acquire(puVar1), iVar2 != 0)) {
      puVar4 = DAT_0037ca80 + 1;
      *DAT_0037ca80 = 0x5e715e28;
      FUN_006370b0(puVar4,1);
      FUN_006370b0(DAT_0037cac8,1);
      __cxa_guard_release(puVar1);
      __aeabi_atexit(DAT_0037ca80,DAT_0037cacc,DAT_0037cad0);
    }
    FUN_0037ad64(DAT_0037ca80);
  }
  if (((*puVar1 & 1) == 0) && (iVar2 = __cxa_guard_acquire(DAT_0037ca7c), iVar2 != 0)) {
    puVar4 = DAT_0037ca80 + 1;
    *DAT_0037ca80 = 0x5e715e28;
    FUN_006370b0(puVar4,1);
    FUN_006370b0(DAT_0037cac8,1);
    __cxa_guard_release(DAT_0037ca7c);
    __aeabi_atexit(DAT_0037ca80,DAT_0037cacc,DAT_0037cad0);
  }
  iVar2 = FUN_0037bf90(param_1,0,DAT_0037ca80);
  if (iVar2 != 0) {
    FUN_004f8ffc(auStack_58,param_1,DAT_0037ca84,DAT_0037ca84,param_2);
    FUN_004f96c8(auStack_58,DAT_0037ca88);
    FUN_004f95a8(auStack_4c,auStack_58);
    FUN_00658f54(auStack_50,auStack_4c);
    FUN_00627f38(auStack_4c);
    FUN_00620200(auStack_48,auStack_50);
    if (((*puVar1 & 1) == 0) && (iVar2 = __cxa_guard_acquire(DAT_0037ca7c), iVar2 != 0)) {
      puVar4 = DAT_0037ca80 + 1;
      *DAT_0037ca80 = 0x5e715e28;
      FUN_006370b0(puVar4,1);
      FUN_006370b0(DAT_0037cac8,1);
      __cxa_guard_release(DAT_0037ca7c);
      __aeabi_atexit(DAT_0037ca80,DAT_0037cacc,DAT_0037cad0);
    }
    iVar2 = FUN_0037c140(param_1,0,DAT_0037ca80);
    if (((iVar2 != 0) && (iVar2 = FUN_00645bb0(auStack_50), iVar2 != 0)) &&
       (iVar2 = FUN_0065f944(auStack_50), iVar2 == 0)) {
      FUN_004f782c(DAT_0037caa8,DAT_0037caac,DAT_0037cac4);
    }
    FUN_00636894(auStack_14,param_1);
    uVar3 = FUN_00637194(param_2 + 4,auStack_14);
    FUN_0062ab18(auStack_40,uVar3);
    FUN_00658f54(auStack_44,auStack_40);
    FUN_00627f38(auStack_40);
    FUN_00636894(auStack_3c,DAT_0037ca8c);
    FUN_00659dc8(auStack_38,auStack_44,auStack_3c);
    FUN_00620248(auStack_44,auStack_38);
    FUN_00627f38(auStack_38);
    iVar2 = FUN_0064f810(auStack_44,auStack_50);
    if (iVar2 == 0) {
      FUN_004f782c(DAT_0037caa8,DAT_0037caac,DAT_0037cac0);
    }
    FUN_00636880(auStack_34,DAT_0037ca90);
    FUN_00659dc8(auStack_30,auStack_50,auStack_34);
    FUN_00620248(auStack_50,auStack_30);
    FUN_00627f38(auStack_30);
    iVar2 = FUN_00645bb0(auStack_50);
    if (iVar2 != 0) {
      if (((*DAT_0037cab4 & 1) == 0) && (iVar2 = __cxa_guard_acquire(), iVar2 != 0)) {
        FUN_0064a3fc(DAT_0037cab8,DAT_0037caf4);
        __cxa_guard_release(DAT_0037cab4);
        __aeabi_atexit(DAT_0037cab8,DAT_0037caf8,DAT_0037cad0);
      }
      FUN_004f8524(auStack_58,param_1,DAT_0037cab8);
      FUN_004f95a8(auStack_2c,auStack_58);
      FUN_00658f54(auStack_28,auStack_2c);
      iVar2 = FUN_0064f810(auStack_50,auStack_28);
      FUN_00627f38(auStack_28);
      FUN_00627f38(auStack_2c);
      if (iVar2 == 0) {
        FUN_004f782c(DAT_0037caa8,DAT_0037caac,DAT_0037cabc);
      }
    }
    FUN_00636880(auStack_24,DAT_0037ca94);
    FUN_00659dc8(auStack_20,auStack_48,auStack_24);
    FUN_00620248(auStack_50,auStack_20);
    FUN_00627f38(auStack_20);
    iVar2 = FUN_00645bb0(auStack_50);
    if (iVar2 != 0) {
      if (((*DAT_0037caa0 & 1) == 0) && (iVar2 = __cxa_guard_acquire(), iVar2 != 0)) {
        FUN_0064a3fc(DAT_0037caa4,DAT_0037cafc);
        __cxa_guard_release(DAT_0037caa0);
        __aeabi_atexit(DAT_0037caa4,DAT_0037caf8,DAT_0037cad0);
      }
      FUN_004f8524(auStack_58,param_1,DAT_0037caa4);
      FUN_004f95a8(auStack_1c,auStack_58);
      FUN_00658f54(auStack_18,auStack_1c);
      iVar2 = FUN_0064f810(auStack_50,auStack_18);
      FUN_00627f38(auStack_18);
      FUN_00627f38(auStack_1c);
      if (iVar2 == 0) {
        FUN_004f782c(DAT_0037caa8,DAT_0037caac,DAT_0037cab0);
      }
    }
    FUN_00627f38(auStack_44);
    FUN_00627f38(auStack_48);
    FUN_00627f38(auStack_50);
    FUN_00627f38(auStack_58);
  }
  if (((*DAT_0037ca98 & 1) == 0) && (iVar2 = __cxa_guard_acquire(), iVar2 != 0)) {
    FUN_0064a3fc(DAT_0037ca9c,DAT_0037cad4);
    FUN_0064a3fc(DAT_0037cad8,DAT_0037cadc);
    FUN_0064a3fc(DAT_0037cae0,DAT_0037cae4);
    FUN_0064a3fc(DAT_0037cae8,DAT_0037caec);
    __cxa_guard_release(DAT_0037ca98);
    __aeabi_atexit(0,DAT_0037caf0,DAT_0037cad0);
  }
  iVar2 = FUN_0062e318(param_1,DAT_0037ca9c);
  if (iVar2 != 0) {
    FUN_0037b91c(param_1);
  }
  sync();
  return;
}

