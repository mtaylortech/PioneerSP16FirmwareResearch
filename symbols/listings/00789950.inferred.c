/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_00789950(int param_1,undefined4 *param_2,int param_3)

{
  float fVar1;
  float extraout_r0;
  float extraout_r0_00;
  float extraout_r0_01;
  undefined4 uVar2;
  uint uVar3;
  int iVar4;
  int iVar5;
  uint in_fpscr;
  float __x;
  float fVar6;
  float fVar7;
  float fVar8;
  float fVar9;
  float extraout_s15;
  undefined1 auStack_68 [24];
  undefined1 auStack_50 [24];
  undefined1 auStack_38 [12];
  undefined1 auStack_2c [4];
  
  if (((int)((uint)*(byte *)(param_1 + 0x6a) << 0x1e) < 0) ||
     ((int)((uint)*(byte *)(param_1 + 0x6a) << 0x1d) < 0)) {
    FUN_00789788(param_1);
    *(byte *)(param_1 + 0x6a) = *(byte *)(param_1 + 0x6a) & 0xf9;
  }
  if (*(int *)(param_1 + 0x3c) == 0) {
    uVar3 = (uint)*(byte *)(param_1 + 0x6c);
    if ((uVar3 == 0) || (param_3 != 0)) {
      FUN_0078a6ac(param_1,param_2);
    }
    else if (uVar3 != 0xff) {
      fVar1 = (float)VectorSignedToFloat(0xff - uVar3,(byte)(in_fpscr >> 0x16) & 3);
      FUN_006cfc2c(param_2,fVar1 / DAT_00789bbc);
      FUN_0078a6ac(param_1,param_2);
      FUN_006cfc7c(param_2);
    }
  }
  else {
    fVar1 = (float)(**(code **)(*(int *)*param_2 + 0x14))();
    VectorSignedToFloat(*(undefined4 *)(param_1 + 0x18),(byte)(in_fpscr >> 0x16) & 3);
    VectorSignedToFloat(*(undefined4 *)(param_1 + 0x1c),(byte)(in_fpscr >> 0x16) & 3);
    fVar6 = floorf(__x);
    fVar6 = ceilf(fVar6);
    ceilf(fVar6);
    uVar3 = -((int)((uint)*(byte *)(param_1 + 0x68) << 0x1d) >> 0x1f);
    if (uVar3 == 0) {
      uVar2 = 2;
    }
    else {
      uVar2 = 1;
    }
    iVar5 = (int)extraout_r0_00 - (int)extraout_r0;
    iVar4 = (int)extraout_r0_01 - (int)extraout_r0;
    FUN_006d3188(auStack_2c,uVar2,iVar5,iVar4,uVar3 ^ 1);
    FUN_006cf768(auStack_38,auStack_2c);
    fVar7 = (float)VectorSignedToFloat(*(undefined4 *)(param_1 + 0x18),(byte)(in_fpscr >> 0x16) & 3)
    ;
    fVar6 = (float)VectorSignedToFloat(iVar5,(byte)(in_fpscr >> 0x16) & 3);
    fVar9 = (float)VectorSignedToFloat(*(undefined4 *)(param_1 + 0x1c),(byte)(in_fpscr >> 0x16) & 3)
    ;
    fVar8 = (float)VectorSignedToFloat(iVar4,(byte)(in_fpscr >> 0x16) & 3);
    FUN_006c67dc(auStack_68,fVar6 / fVar7,fVar8 / fVar9);
    FUN_006cfbc4(auStack_38,auStack_68);
    FUN_0078a6ac(param_1,auStack_38);
    FUN_006cf7b8(auStack_38);
    FUN_006cfa70(param_2);
    FUN_006c67fc(auStack_50,1.0 / fVar1);
    FUN_006cfbc4(param_2,auStack_50);
    fVar6 = extraout_s15;
    if (param_3 != 0) {
      fVar6 = 1.0;
    }
    if (param_3 == 0) {
      fVar6 = (float)VectorSignedToFloat(0xff - (uint)*(byte *)(param_1 + 0x6c),
                                         (byte)(in_fpscr >> 0x16) & 3);
      fVar6 = fVar6 / DAT_00789bbc;
    }
    (**(code **)**(undefined4 **)(param_1 + 0x3c))
              (*(undefined4 **)(param_1 + 0x3c),auStack_2c,param_2,fVar1,fVar6);
    FUN_006cfaa8(param_2);
    FUN_00707778(auStack_2c);
  }
  return;
}

