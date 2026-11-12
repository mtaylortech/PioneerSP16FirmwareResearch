/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_004c8990(int param_1,undefined4 param_2)

{
  int iVar1;
  uint in_fpscr;
  float fVar2;
  float fVar3;
  float fVar4;
  undefined8 local_40;
  undefined8 local_38;
  undefined4 local_30;
  undefined4 local_2c;
  undefined8 local_28;
  undefined1 auStack_1c [4];
  undefined1 auStack_18 [4];
  undefined1 auStack_14 [8];
  
  local_40 = DAT_004c8b08;
  local_38 = DAT_004c8b10;
  FUN_004f4878(auStack_1c,0xc);
  FUN_0070acf0(param_2,auStack_1c);
  FUN_006a0280(auStack_1c);
  FUN_006cfddc(param_2,&local_40);
  iVar1 = *(int *)(param_1 + 0xb4) - *(int *)(param_1 + 0xb0);
  if (iVar1 < 1) {
    iVar1 = 0;
  }
  else {
    fVar4 = (float)VectorSignedToFloat(iVar1,(byte)(in_fpscr >> 0x16) & 3);
    fVar2 = (float)VectorSignedToFloat(*(int *)(param_1 + 0xb8) - *(int *)(param_1 + 0xb0),
                                       (byte)(in_fpscr >> 0x16) & 3);
    fVar3 = (float)VectorSignedToFloat((int)local_38,(byte)(in_fpscr >> 0x16) & 3);
    iVar1 = (int)(fVar3 * (fVar2 / fVar4));
  }
  FUN_004f4878(auStack_18,0xd);
  FUN_0070acf0(param_2,auStack_18);
  FUN_006a0280(auStack_18);
  local_28 = CONCAT44(local_38._4_4_,iVar1);
  local_30 = (int)local_40;
  local_2c = local_40._4_4_;
  FUN_006cfddc(param_2,&local_30);
  FUN_004f4878(auStack_14,0xb);
  FUN_0070acf0(param_2,auStack_14);
  FUN_006a0280(auStack_14);
  FUN_006cfe10(param_2,(int)local_40 + -2,local_40._4_4_,1,local_38._4_4_);
  FUN_006cfe10(param_2,(int)local_40 + (int)local_38 + 2,local_40._4_4_,1,local_38._4_4_);
  return;
}

