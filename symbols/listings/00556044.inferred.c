/* INFERRED PSEUDOCODE; names/types/indirect targets need instruction checks. No target execution. */

int * FUN_00556044(int *param_1)

{
  int iVar1;
  void *pvVar2;
  
  *param_1 = DAT_005560b4;
  FUN_006967dc(param_1 + 1);
  iVar1 = DAT_005560b8;
  param_1[2] = 0;
  param_1[1] = iVar1 + 0x18;
  *param_1 = iVar1;
  pvVar2 = operator_new(0x103c);
  FUN_00556880();
  param_1[2] = (int)pvVar2;
  return param_1;
}

