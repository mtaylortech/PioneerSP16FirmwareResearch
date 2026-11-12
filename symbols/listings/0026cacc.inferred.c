/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void candidate_0026cacc(int param_1,undefined4 *param_2,undefined4 *param_3,undefined4 *param_4)

{
  undefined4 *unaff_r4;
  int unaff_r5;
  uint unaff_r6;
  bool in_ZR;
  undefined4 uStack00000000;
  undefined4 uStack00000004;
  undefined4 *puStack00000008;
  char acStack_424 [1040];
  undefined1 auStack_10 [8];
  
  if (((!in_ZR) && ((unaff_r6 & 3) == 0)) && (*(int *)(param_1 + unaff_r5) == 0x5e715e28)) {
    *param_2 = *(undefined4 *)(param_1 + 0xc0);
    *param_3 = *(undefined4 *)(param_1 + 200);
    *param_4 = *(undefined4 *)(param_1 + 0xc4);
    *unaff_r4 = *(undefined4 *)(param_1 + 0xcc);
    return;
  }
  uStack00000004 = _UNK_0026cb18;
  uStack00000000 = _UNK_0026cb14;
  puStack00000008 = param_4;
  vsprintf(acStack_424,_UNK_0026cb10,&stack0x00000000);
  FUN_00636880(auStack_10,acStack_424);
  FUN_004f7608(auStack_10);
  return;
}

