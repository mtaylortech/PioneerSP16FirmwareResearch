/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_0078f8d8(int param_1,undefined8 *param_2)

{
  int *piVar1;
  float extraout_r0;
  float extraout_r0_00;
  float extraout_r0_01;
  float extraout_r0_02;
  int iVar2;
  code *pcVar3;
  uint in_fpscr;
  float fVar4;
  int iVar5;
  undefined8 local_78;
  undefined8 local_70;
  undefined8 local_68;
  undefined8 local_60;
  undefined8 local_58;
  undefined8 local_50;
  undefined1 auStack_48 [8];
  undefined4 local_40;
  undefined4 local_3c;
  undefined1 auStack_38 [20];
  
  if ((*(byte *)(param_1 + 0x68) & 1) == 0) {
    iVar2 = *(int *)(param_1 + 0xc);
    if (iVar2 != 0) {
      local_68 = *param_2;
      local_60 = param_2[1];
      FUN_0078f660(auStack_38,param_1,&local_68);
      FUN_0078fb14(iVar2,auStack_38);
    }
  }
  else {
    piVar1 = (int *)FUN_0078ddc8();
    if (piVar1 != (int *)0x0) {
      fVar4 = (float)(**(code **)(*piVar1 + 0x20))(auStack_48,piVar1);
      VectorSignedToFloat(*(undefined4 *)(param_1 + 0x18),(byte)(in_fpscr >> 0x16) & 3);
      VectorSignedToFloat(local_40,(byte)(in_fpscr >> 0x16) & 3);
      VectorSignedToFloat(local_3c,(byte)(in_fpscr >> 0x16) & 3);
      VectorSignedToFloat(*(undefined4 *)(param_1 + 0x1c),(byte)(in_fpscr >> 0x16) & 3);
      VectorSignedToFloat(*(undefined4 *)param_2,(byte)(in_fpscr >> 0x16) & 3);
      VectorSignedToFloat(*(undefined4 *)(param_2 + 1),(byte)(in_fpscr >> 0x16) & 3);
      VectorSignedToFloat(*(undefined4 *)((int)param_2 + 4),(byte)(in_fpscr >> 0x16) & 3);
      VectorSignedToFloat(*(undefined4 *)((int)param_2 + 0xc),(byte)(in_fpscr >> 0x16) & 3);
      fVar4 = floorf(fVar4);
      iVar2 = (int)extraout_r0;
      fVar4 = floorf(fVar4);
      iVar5 = (int)extraout_r0_00;
      fVar4 = ceilf(fVar4);
      ceilf(fVar4);
      local_78 = CONCAT44(iVar5,iVar2);
      local_70 = CONCAT44((int)extraout_r0_02 - iVar5,(int)extraout_r0_01 - iVar2);
      pcVar3 = *(code **)(*piVar1 + 0x80);
      if (*(int *)(param_1 + 0x24) == 0) {
        local_58 = CONCAT44(iVar5,iVar2);
        local_50 = CONCAT44((int)extraout_r0_02 - iVar5,(int)extraout_r0_01 - iVar2);
      }
      else {
        FUN_0072f018(&local_58,&local_78);
      }
      (*pcVar3)(piVar1,&local_58);
    }
  }
  return;
}

