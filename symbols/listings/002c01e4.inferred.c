/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void candidate_002c01e4(int param_1,int param_2)

{
  int iVar1;
  int iVar2;
  void *apvStack_5c [2];
  int iStack_54;
  void *apvStack_50 [2];
  int iStack_48;
  void *apvStack_44 [2];
  int iStack_3c;
  void *apvStack_38 [2];
  int iStack_30;
  void *apvStack_2c [2];
  int iStack_24;
  void *apvStack_20 [2];
  int iStack_18;
  undefined1 auStack_14 [8];
  
  iVar1 = param_1 + -0x28;
  FUN_0062ab18(auStack_14,*(int *)(param_2 + 0x14) + 4);
  iVar2 = FUN_0062e318(auStack_14,PTR_DAT_002c0440);
  if (iVar2 != 0) {
    FUN_002c0678(apvStack_5c,*(undefined4 *)(param_1 + 0x18));
    free(apvStack_5c[0]);
    if ((0 < iStack_54) && (iVar2 = FUN_002bffb0(iVar1,1), iVar2 != 0)) {
      FUN_0069c37c(param_1 + 4,1,500);
    }
  }
  iVar2 = FUN_0062e318(auStack_14,PTR_DAT_002c0444);
  if (iVar2 != 0) {
    FUN_002c0678(apvStack_50,*(undefined4 *)(param_1 + 0x18));
    free(apvStack_50[0]);
    if ((1 < iStack_48) && (iVar2 = FUN_002bffb0(iVar1,2), iVar2 != 0)) {
      FUN_0069c37c(param_1 + 4,2,500);
    }
  }
  iVar2 = FUN_0062e318(auStack_14,PTR_DAT_002c0448);
  if (iVar2 != 0) {
    FUN_002c0678(apvStack_44,*(undefined4 *)(param_1 + 0x18));
    free(apvStack_44[0]);
    if ((2 < iStack_3c) && (iVar2 = FUN_002bffb0(iVar1,3), iVar2 != 0)) {
      FUN_0069c37c(param_1 + 4,3,500);
    }
  }
  iVar2 = FUN_0062e318(auStack_14,PTR_DAT_002c044c);
  if (iVar2 != 0) {
    FUN_002c0678(apvStack_38,*(undefined4 *)(param_1 + 0x18));
    free(apvStack_38[0]);
    if ((3 < iStack_30) && (iVar2 = FUN_002bffb0(iVar1,4), iVar2 != 0)) {
      FUN_0069c37c(param_1 + 4,4,500);
    }
  }
  iVar2 = FUN_0062e318(auStack_14,PTR_DAT_002c0450);
  if (iVar2 != 0) {
    FUN_002c0678(apvStack_2c,*(undefined4 *)(param_1 + 0x18));
    free(apvStack_2c[0]);
    if ((4 < iStack_24) && (iVar2 = FUN_002bffb0(iVar1,5), iVar2 != 0)) {
      FUN_0069c37c(param_1 + 4,5,500);
    }
  }
  iVar2 = FUN_0062e318(auStack_14,PTR_DAT_002c0454);
  if (iVar2 != 0) {
    FUN_002c0678(apvStack_20,*(undefined4 *)(param_1 + 0x18));
    free(apvStack_20[0]);
    if ((5 < iStack_18) && (iVar1 = FUN_002bffb0(iVar1,6), iVar1 != 0)) {
      FUN_0069c37c(param_1 + 4,6,500);
    }
  }
  FUN_00627f38(auStack_14);
  return;
}

