/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

undefined4 *
FUN_004b07a4(undefined4 *param_1,undefined4 param_2,int param_3,undefined4 param_4,int param_5)

{
  code *pcVar1;
  undefined4 uVar2;
  
  *param_1 = param_2;
  param_1[3] = 0;
  if (*(int *)(param_3 + 8) != 0) {
    uVar2 = *(undefined4 *)(param_3 + 0xc);
    param_1[3] = *(int *)(param_3 + 8);
    pcVar1 = *(code **)(param_3 + 8);
    param_1[4] = uVar2;
    (*pcVar1)(param_1 + 1,param_3,2,pcVar1,param_4);
  }
  param_1[5] = param_4;
  param_1[8] = 0;
  if (*(int *)(param_5 + 8) != 0) {
    uVar2 = *(undefined4 *)(param_5 + 0xc);
    param_1[8] = *(int *)(param_5 + 8);
    pcVar1 = *(code **)(param_5 + 8);
    param_1[9] = uVar2;
    (*pcVar1)(param_1 + 6,param_5,2);
  }
  return param_1;
}

