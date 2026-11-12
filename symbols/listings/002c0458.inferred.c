/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

undefined4 *
FUN_002c0458(undefined4 *param_1,undefined4 *param_2,undefined4 param_3,undefined4 param_4)

{
  undefined4 uVar1;
  undefined4 uVar2;
  undefined4 uVar3;
  
  uVar3 = DAT_002c0520;
  *param_1 = DAT_002c051c;
  param_1[1] = DAT_002c0524;
  param_1[2] = param_2[2];
  param_1[3] = param_2[3];
  *param_1 = param_2[1];
  param_1[1] = uVar3;
  param_1[2] = param_2[4];
  uVar2 = param_2[5];
  param_1[4] = param_3;
  param_1[9] = param_4;
  uVar1 = DAT_002c052c;
  uVar3 = DAT_002c0528;
  param_1[3] = uVar2;
  param_1[8] = uVar3;
  param_1[10] = uVar1;
  param_1[5] = 0;
  param_1[6] = 0;
  param_1[7] = 0;
  FUN_0069760c(param_1 + 0xb);
  uVar3 = *param_2;
  param_1[1] = &PTR_LAB_008921a8;
  *param_1 = uVar3;
  param_1[2] = param_2[6];
  uVar3 = param_2[7];
  param_1[8] = &DAT_00892200;
  param_1[10] = &PTR_LAB_00892210;
  param_1[3] = uVar3;
  param_1[0xb] = &DAT_00892240;
  param_1[0x10] = 0;
  return param_1;
}

