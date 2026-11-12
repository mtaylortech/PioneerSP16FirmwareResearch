/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

undefined4 FUN_0069653c(undefined4 param_1)

{
  int *piVar1;
  int *piVar2;
  undefined4 uVar3;
  int iVar4;
  int iVar5;
  undefined1 auStack_24 [4];
  undefined1 auStack_20 [4];
  undefined1 auStack_1c [8];
  
  piVar1 = DAT_0069662c;
  FUN_0062ab08(auStack_24);
  piVar2 = DAT_00696630;
  if (1 < *piVar1) {
    iVar5 = 1;
    do {
      FUN_0064a3fc(auStack_20,*(undefined4 *)(*piVar2 + iVar5 * 4));
      iVar4 = FUN_00630ea8(auStack_20,0x20);
      if ((iVar4 != 0) && (iVar4 = FUN_0063485c(auStack_20), iVar4 == 0)) {
        FUN_006349ec(auStack_1c,auStack_20,0x22);
        FUN_0062ad54(auStack_20,auStack_1c);
        FUN_00627f38(auStack_1c);
      }
      uVar3 = thunk_FUN_0062eabc(auStack_24,auStack_20);
      FUN_0062f964(uVar3,0x20);
      iVar5 = iVar5 + 1;
      FUN_00627f38(auStack_20);
    } while (iVar5 < *piVar1);
  }
  FUN_00634b60(param_1,auStack_24);
  FUN_00627f38(auStack_24);
  return param_1;
}

