/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

undefined4
FUN_0039025c(undefined4 param_1,undefined4 param_2,undefined4 param_3,undefined4 param_4,
            char param_5)

{
  undefined4 uVar1;
  undefined4 uVar2;
  int iVar3;
  uint in_fpscr;
  undefined1 auStack_28 [12];
  int local_1c;
  undefined1 auStack_18 [4];
  undefined1 auStack_14 [8];
  
  iVar3 = DAT_00390380 + -4;
  if (param_5 == '\0') {
    iVar3 = DAT_00390380;
  }
  FUN_0038fef4(&local_1c,param_2,param_3,iVar3);
  if (local_1c == 0) {
    FUN_006d3480(auStack_18,&local_1c);
    FUN_006cf768(auStack_28,auStack_18);
    FUN_006c1630(auStack_14,DAT_00390384);
    FUN_0070acf0(auStack_28,auStack_14);
    FUN_006a0280(auStack_14);
    uVar1 = FUN_006d3360(&local_1c);
    uVar2 = FUN_006d3370(&local_1c);
    uVar1 = VectorSignedToFloat(uVar1,(byte)(in_fpscr >> 0x16) & 3);
    uVar2 = VectorSignedToFloat(uVar2,(byte)(in_fpscr >> 0x16) & 3);
    FUN_006d0c90(auStack_28,0,0,uVar1,uVar2,0x40000000,0x40000000);
    FUN_006d32fc(param_1,auStack_18);
    FUN_006cf7b8(auStack_28);
    FUN_00707778(auStack_18);
  }
  else {
    FUN_006d32fc(param_1,&local_1c);
  }
  FUN_00707778(&local_1c);
  return param_1;
}

