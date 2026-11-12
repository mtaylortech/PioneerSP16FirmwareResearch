/* INFERRED PSEUDOCODE; names/types/indirect targets need instruction checks. No target execution. */

undefined4 FUN_005560bc(int param_1,uint param_2)

{
  undefined4 uVar1;
  
  if (param_2 < *(uint *)(*(int *)(param_1 + 8) + 0xc)) {
    uVar1 = *(undefined4 *)(*(int *)(*(int *)(param_1 + 8) + 4) + param_2 * 4);
  }
  else {
    uVar1 = 0;
  }
  return uVar1;
}

