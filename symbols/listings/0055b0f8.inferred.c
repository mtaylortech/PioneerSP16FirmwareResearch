/* INFERRED PSEUDOCODE; names/types/indirect targets need instruction checks. No target execution. */

void FUN_0055b0f8(undefined4 *param_1)

{
  undefined4 uVar1;
  
  uVar1 = DAT_0055b140;
  *(undefined1 *)(param_1 + 1) = 0;
  *(undefined1 *)(param_1 + 3) = 0;
  *param_1 = uVar1;
  param_1[2] = 0xffffffff;
  *(undefined1 *)((int)param_1 + 0xd) = 0;
  *(undefined1 *)((int)param_1 + 0xe) = 0;
  *(undefined1 *)((int)param_1 + 0xf) = 0;
  *(undefined8 *)(param_1 + 4) = 0;
  param_1[6] = 0;
  param_1[7] = 0;
  param_1[8] = 0;
  param_1[9] = 0;
  return;
}

