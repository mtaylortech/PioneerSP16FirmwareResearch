/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void candidate_0026caa0(int param_1,int *param_2,int *param_3,int *param_4,int *param_5)

{
  int *piVar1;
  uint uVar2;
  char acStack_430 [1040];
  undefined1 *puStack_20;
  undefined1 auStack_1c [8];
  
  piVar1 = *(int **)(param_1 + 300);
  if ((piVar1 != (int *)0x0) && (((uint)piVar1 & 3) == 0)) {
    uVar2 = (int)piVar1 + *(int *)(*piVar1 + -0xc);
    if ((uVar2 != 0) &&
       (((uVar2 & 3) == 0 && (*(int *)((int)piVar1 + *(int *)(*piVar1 + -0xc)) == 0x5e715e28)))) {
      *param_2 = piVar1[0x30];
      *param_3 = piVar1[0x32];
      *param_4 = piVar1[0x31];
      *param_5 = piVar1[0x33];
      return;
    }
  }
  puStack_20 = &stack0xfffffff4;
  vsprintf(acStack_430,_UNK_0026cb10,puStack_20);
  FUN_00636880(auStack_1c,acStack_430);
  FUN_004f7608(auStack_1c);
  return;
}

