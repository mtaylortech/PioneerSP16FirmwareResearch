/* INFERRED PSEUDOCODE; names/types/indirect targets need instruction checks. No target execution. */

undefined4 FUN_0069a9e8(undefined4 param_1)

{
  int iVar1;
  int iVar2;
  void *pvVar3;
  
  iVar1 = DAT_0069aa40;
  iVar2 = *(int *)(DAT_0069aa40 + 0x5c) + -1;
  *(int *)(DAT_0069aa40 + 0x5c) = iVar2;
  if (iVar2 != 0) {
    return param_1;
  }
  FUN_0069693c();
  pvVar3 = *(void **)(iVar1 + 4);
  if (pvVar3 != (void *)0x0) {
    FUN_0069a828(pvVar3);
    operator_delete(pvVar3);
  }
  *(undefined4 *)(iVar1 + 4) = 0;
  return param_1;
}

