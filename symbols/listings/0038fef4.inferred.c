/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

undefined4 FUN_0038fef4(undefined4 param_1,int param_2,undefined4 param_3,undefined4 param_4)

{
  undefined4 uVar1;
  int iVar2;
  undefined1 auStack_54 [12];
  undefined4 local_48 [2];
  undefined1 auStack_40 [4];
  undefined1 auStack_3c [4];
  undefined1 auStack_38 [4];
  undefined1 auStack_34 [4];
  undefined1 auStack_30 [4];
  undefined1 auStack_2c [4];
  undefined1 auStack_28 [4];
  undefined1 auStack_24 [4];
  undefined1 auStack_20 [4];
  undefined1 auStack_1c [8];
  
  FUN_00627ba0(auStack_40,param_4);
  uVar1 = FUN_0068b048(param_3,auStack_40);
  FUN_006280c8(auStack_40);
  iVar2 = FUN_0061f6bc(uVar1);
  if (iVar2 == 0) {
    FUN_0061f85c(auStack_3c,uVar1);
    FUN_00636894(auStack_38,DAT_00390138);
    iVar2 = FUN_00632744(auStack_3c,auStack_38);
    if (iVar2 == 0) {
      FUN_00636894(auStack_1c,auStack_3c);
      FUN_00659dc8(auStack_20,param_2 + 0x90,auStack_1c);
      iVar2 = FUN_00646364(auStack_20);
      if (iVar2 == 0) {
        FUN_004f782c(DAT_00390144,DAT_00390148,DAT_0039014c);
        FUN_00627f38(auStack_20);
        FUN_00627f38(auStack_3c);
        goto LAB_003900a8;
      }
      FUN_0070974c(param_1,auStack_20);
      FUN_00627f38(auStack_20);
    }
    else {
      FUN_006d3188(auStack_34,2,100,100,0);
      FUN_006cf768(auStack_54,auStack_34);
      FUN_006c1630(auStack_30,DAT_0039013c);
      FUN_0070c1a8(auStack_54,auStack_30);
      FUN_006a0280(auStack_30);
      FUN_006c1630(auStack_2c,DAT_00390140);
      FUN_0070acf0(auStack_54,auStack_2c);
      FUN_006a0280(auStack_2c);
      FUN_00636894(auStack_28,DAT_00390138);
      FUN_0063441c(auStack_24,auStack_3c,auStack_28,0,0);
      local_48[0] = 0x21;
      FUN_00714ca0(auStack_54,auStack_24,0,0,100,100,local_48,1);
      FUN_00627f38(auStack_24);
      FUN_006d32fc(param_1,auStack_34);
      FUN_006cf7b8(auStack_54);
      FUN_00707778(auStack_34);
    }
    FUN_00627f38(auStack_3c);
  }
  else {
LAB_003900a8:
    FUN_006d32c4(param_1,DAT_00390150);
  }
  return param_1;
}

