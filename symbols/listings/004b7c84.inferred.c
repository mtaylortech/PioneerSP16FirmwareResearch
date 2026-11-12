/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

int * FUN_004b7c84(undefined4 param_1,uint param_2)

{
  undefined4 uVar1;
  int *piVar2;
  int iVar3;
  int iVar4;
  int iVar5;
  undefined1 auStack_20 [4];
  undefined1 auStack_1c [8];
  
  if (((*DAT_004b7e6c & 1) == 0) && (iVar3 = __cxa_guard_acquire(DAT_004b7e6c), iVar3 != 0)) {
    FUN_00666e84(DAT_004b7e74,DAT_004b7e88);
    FUN_00666e84(DAT_004b7e8c,DAT_004b7e90);
    FUN_00666e84(DAT_004b7e94,DAT_004b7e98);
    FUN_00666e84(DAT_004b7e9c,DAT_004b7ea0);
    FUN_00666e84(DAT_004b7ea4,DAT_004b7ea8);
    FUN_00666e84(DAT_004b7eac,DAT_004b7eb0);
    __cxa_guard_release(DAT_004b7e6c);
    __aeabi_atexit(0,DAT_004b7eb4,DAT_004b7eb8);
  }
  if (param_2 < 6) {
    piVar2 = operator_new(0xe0);
    uVar1 = DAT_004b7e70;
    piVar2[0x37] = 0x5e715e28;
    FUN_0064a3fc(auStack_20,uVar1);
    FUN_0062ab18(auStack_1c,auStack_20);
    FUN_004c8d3c(piVar2,DAT_004b7e78,param_1,DAT_004b7e74 + param_2 * 4,auStack_1c);
    FUN_00627f38(auStack_1c);
    iVar4 = DAT_004b7e80;
    iVar3 = DAT_004b7e7c;
    piVar2[0x26] = DAT_004b7e7c + 0x10c;
    *piVar2 = iVar3;
    piVar2[0x1c] = iVar4;
    piVar2[0x25] = iVar4 + 0x10;
    FUN_00627f38(auStack_20);
    iVar3 = DAT_004b7e84 + 0x108;
    iVar4 = DAT_004b7e84 + 0x118;
    iVar5 = DAT_004b7e84 + 0x140;
    *piVar2 = DAT_004b7e84;
    piVar2[0x1c] = iVar3;
    piVar2[0x25] = iVar4;
    piVar2[0x26] = iVar5;
  }
  else {
    piVar2 = (int *)0x0;
    FUN_004f782c(DAT_004b7ebc,DAT_004b7ec0,DAT_004b7ec4);
  }
  return piVar2;
}

