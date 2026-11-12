/* INFERRED PSEUDOCODE; names/types/indirect targets need instruction checks. No target execution. */

undefined4 * FUN_006958e0(undefined4 *param_1)

{
  int *piVar1;
  
  piVar1 = (int *)param_1[3];
  *param_1 = DAT_0069591c;
  *DAT_00695920 = 0;
  if (piVar1 != (int *)0x0) {
    (**(code **)(*piVar1 + 4))();
  }
  return param_1;
}

