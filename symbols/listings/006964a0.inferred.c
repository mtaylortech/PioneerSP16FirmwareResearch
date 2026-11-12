/* INFERRED PSEUDOCODE; names/types/indirect targets need instruction checks. No target execution. */

void FUN_006964a0(undefined4 *param_1)

{
  undefined4 uVar1;
  
  uVar1 = DAT_006964cc;
  param_1[1] = 0;
  *param_1 = uVar1;
  param_1[3] = 0;
  *(undefined1 *)(param_1 + 2) = 1;
  DAT_00f6e644 = param_1;
  return;
}

