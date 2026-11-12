/* INFERRED PSEUDOCODE; names/types/indirect targets need instruction checks. No target execution. */

void FUN_0069e740(int param_1)

{
  int iVar1;
  undefined4 extraout_r1;
  int *piVar2;
  code *pcVar3;
  undefined1 auStack_2c [4];
  undefined1 auStack_28 [4];
  undefined1 auStack_24 [4];
  undefined1 auStack_20 [4];
  undefined1 auStack_1c [4];
  
  if (*(int *)(param_1 + 0x10) != 0) {
    (**(code **)(param_1 + 0x14))(param_1 + 8);
    return;
  }
  std::__throw_bad_function_call();
  piVar2 = (int *)*DAT_0069e84c;
  if (piVar2 != (int *)0x0) {
    (**(code **)(*piVar2 + 8))(auStack_2c,piVar2);
    FUN_0062ab18(auStack_28,auStack_2c);
    FUN_0062f844(auStack_24,auStack_28,DAT_0069e850);
    FUN_00636894(auStack_20,auStack_24);
    iVar1 = FUN_00632744(extraout_r1,auStack_20);
    FUN_00627f38(auStack_24);
    FUN_00627f38(auStack_28);
    if (iVar1 != 0) {
      pcVar3 = *(code **)(*piVar2 + 0x1c);
      iVar1 = FUN_0062dd70(auStack_2c);
      FUN_006339d4(auStack_1c,extraout_r1,iVar1 + 1);
      (*pcVar3)(piVar2,auStack_1c);
      FUN_00627f38(auStack_1c);
    }
    FUN_00627f38(auStack_2c);
  }
                    /* WARNING: Could not recover jumptable at 0x0069e824. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*(code *)0x69e764)();
  return;
}

