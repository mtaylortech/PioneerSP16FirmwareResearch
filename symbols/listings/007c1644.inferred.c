/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_007c1644(int param_1,int param_2)

{
  int iVar1;
  int *piVar2;
  int *piVar3;
  int *piVar4;
  
  piVar4 = *(int **)(param_1 + 0x28);
  if (piVar4 == piVar4 + *(int *)(param_1 + 0x30)) {
LAB_007c168c:
    iVar1 = -1;
  }
  else {
    piVar2 = piVar4;
    piVar3 = piVar4;
    if (param_2 == *piVar4) {
      iVar1 = 0;
    }
    else {
      do {
        piVar3 = piVar3 + 1;
        if (piVar4 + *(int *)(param_1 + 0x30) == piVar3) goto LAB_007c168c;
        piVar2 = piVar2 + 1;
      } while (param_2 != *piVar2);
      iVar1 = (int)piVar3 - (int)piVar4 >> 2;
    }
  }
  FUN_007c1324(param_1,iVar1,1,1);
  return;
}

