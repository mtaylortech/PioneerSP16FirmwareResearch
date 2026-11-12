/* INFERRED PSEUDOCODE; names/types/indirect targets need instruction checks. No target execution. */

bool FUN_00696634(int *param_1)

{
  undefined4 uVar1;
  int *piVar2;
  int *piVar3;
  int iVar4;
  undefined1 auStack_28 [4];
  undefined1 auStack_24 [4];
  undefined1 auStack_20 [4];
  undefined1 auStack_1c [4];
  undefined1 auStack_18 [4];
  undefined1 auStack_14 [8];
  
  (**(code **)(*param_1 + 8))(auStack_28,param_1);
  piVar2 = operator_new(0x24);
  uVar1 = DAT_00696798;
  *piVar2 = DAT_00696794;
  FUN_0064af54(auStack_24,uVar1,auStack_28);
  FUN_00646dc0(piVar2 + 1,auStack_24);
  FUN_00627f38(auStack_24);
  piVar3 = (int *)param_1[3];
  if ((piVar2 != piVar3) && (param_1[3] = (int)piVar2, piVar3 != (int *)0x0)) {
    (**(code **)(*piVar3 + 4))();
  }
  FUN_00627f38(auStack_28);
  iVar4 = FUN_0065c594(param_1[3] + 4,0);
  if (iVar4 == 0) {
    (**(code **)(*(int *)*DAT_0069679c + 8))(auStack_1c);
    FUN_0062f844(auStack_18,auStack_1c,DAT_006967a0);
    FUN_0069653c(auStack_20);
    FUN_0062f808(auStack_14,auStack_18,auStack_20);
    FUN_00627f38(auStack_14);
    FUN_00627f38(auStack_20);
    FUN_00627f38(auStack_18);
    FUN_00627f38(auStack_1c);
  }
  return iVar4 == 0;
}

