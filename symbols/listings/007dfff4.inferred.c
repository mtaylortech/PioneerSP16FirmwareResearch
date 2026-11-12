/* INFERRED PSEUDOCODE; names/types/indirect targets need instruction checks. No target execution. */

undefined4 FUN_007dfff4(int *param_1,undefined4 param_2,undefined4 param_3,undefined4 param_4)

{
  int iVar1;
  int *piVar2;
  undefined4 uVar3;
  int iVar4;
  
  if (param_1 != (int *)0x0) {
    iVar4 = 0;
    piVar2 = param_1;
    do {
      iVar4 = iVar4 + 1;
      iVar1 = FUN_007dfd20(piVar2,param_2,param_3);
      if (iVar1 != 0) {
        return 1;
      }
      piVar2 = (int *)(**(code **)(*piVar2 + 8))(piVar2);
      if (piVar2 == param_1 || 100 < iVar4) {
        if (piVar2 != (int *)0x0) {
          return 0;
        }
        break;
      }
    } while (piVar2 != (int *)0x0);
  }
  if (*DAT_007e00bc == 0) {
    return 0;
  }
  iVar4 = __dynamic_cast(*DAT_007e00bc,DAT_007e00c0,DAT_007e00c4,0);
  if (iVar4 != 0) {
    uVar3 = FUN_007dfd20(iVar4 + 0x10,param_2,param_3,param_4);
    return uVar3;
  }
  return 0;
}

