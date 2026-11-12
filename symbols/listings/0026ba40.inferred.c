/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_0026ba40(int param_1,int *param_2,int param_3,undefined4 param_4)

{
  uint uVar1;
  int iVar2;
  int *piVar3;
  
  piVar3 = *(int **)(param_1 + 0x128);
  if ((piVar3 != (int *)0x0) && (((uint)piVar3 & 3) == 0)) {
    uVar1 = (int)piVar3 + *(int *)(*piVar3 + -0xc);
    if ((uVar1 != 0) &&
       (((uVar1 & 3) == 0 && (*(int *)((int)piVar3 + *(int *)(*piVar3 + -0xc)) == 0x5e715e28)))) {
      iVar2 = (**(code **)(*param_2 + 8))(param_2);
      if (iVar2 != 0) {
        return;
      }
      iVar2 = FUN_002f3b40(param_1 + 0x20);
      if (iVar2 != 2) {
        if (param_3 != 0) {
          *(byte *)(param_1 + 0x6a8) = *(byte *)(param_1 + 0x6a8) ^ 1;
        }
        return;
      }
      return;
    }
  }
  FUN_004f782c(DAT_0026badc,DAT_0026bae0,DAT_0026bae4,param_4);
  return;
}

