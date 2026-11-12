/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_00394614(int *param_1,code *param_2,uint param_3,undefined4 param_4)

{
  int iVar1;
  int iVar2;
  int iVar3;
  
  iVar2 = param_1[2];
  if (0 < iVar2) {
    iVar1 = (int)param_3 >> 1;
    iVar3 = iVar2;
    if ((param_3 & 1) == 0) {
      while (((iVar3 = iVar3 + -1, iVar3 < iVar2 || (iVar3 = iVar2 + -1, -1 < iVar3)) &&
             ((*param_2)(*(int *)(*param_1 + iVar3 * 4) + iVar1,param_4), 0 < iVar3))) {
        iVar2 = param_1[2];
      }
    }
    else {
      while (((iVar3 = iVar3 + -1, iVar3 < iVar2 || (iVar3 = iVar2 + -1, -1 < iVar3)) &&
             (iVar2 = *(int *)(*param_1 + iVar3 * 4),
             (**(code **)(param_2 + *(int *)(iVar2 + iVar1)))(iVar2 + iVar1,param_4), 0 < iVar3))) {
        iVar2 = param_1[2];
      }
    }
  }
  return;
}

