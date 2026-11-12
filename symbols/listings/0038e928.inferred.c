/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

int * FUN_0038e928(int *param_1,undefined4 param_2,undefined4 param_3)

{
  int iVar1;
  int iVar2;
  int iVar3;
  int iVar4;
  undefined8 local_38;
  undefined8 local_30;
  undefined1 auStack_28 [4];
  undefined1 auStack_24 [4];
  undefined1 auStack_20 [4];
  undefined1 auStack_1c [4];
  
  FUN_007c4270(param_1,DAT_0038eab8);
  iVar1 = DAT_0038eabc;
  iVar4 = DAT_0038eabc + 0x10c;
  iVar3 = DAT_0038eabc + 300;
  iVar2 = DAT_0038eabc + 0x16c;
  param_1[0x20] = DAT_0038eabc + 0x158;
  param_1[0x1e] = iVar4;
  param_1[0x1f] = iVar3;
  param_1[0x33] = iVar2;
  *param_1 = iVar1;
  param_1[0x34] = iVar1 + 400;
  param_1[0x1c] = iVar1 + 0xf4;
  param_1[0x35] = 0;
  FUN_006c1618(param_1 + 0x36);
  FUN_006c1618(param_1 + 0x37);
  FUN_006c1618(param_1 + 0x38);
  FUN_00760d50(param_1,param_2);
  FUN_00760eb0(param_1,0,0);
  FUN_0062ab18(auStack_20,param_3);
  FUN_004fc4c0(auStack_28,auStack_20);
  FUN_00627f38(auStack_20);
  FUN_00701850(auStack_24);
  FUN_004fb844(auStack_1c,auStack_28,0x41b00000,0);
  FUN_007013a8(auStack_24,auStack_1c);
  FUN_0070ea3c(auStack_1c);
  FUN_00791b48(param_1,auStack_24);
  local_38 = DAT_0038eab0;
  local_30 = DAT_0038eab0;
  FUN_00791ac8(param_1,&local_38);
  FUN_0070ea3c(auStack_24);
  FUN_00627f38(auStack_28);
  return param_1;
}

