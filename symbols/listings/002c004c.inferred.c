/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void candidate_002c004c(int *param_1,int *param_2,undefined4 param_3)

{
  int iVar1;
  void *__ptr;
  int iVar2;
  int iVar3;
  int iVar4;
  int iVar5;
  
  iVar1 = (**(code **)(*param_2 + 8))(param_2);
  if (iVar1 < 1) {
    return;
  }
  if (6 < iVar1) {
    return;
  }
  iVar4 = param_1[0x10];
  iVar3 = *(int *)(iVar4 + 0xb8);
  if (iVar3 == 0) {
    __ptr = (void *)0x0;
  }
  else if (iVar3 < 1) {
    __ptr = (void *)0x0;
  }
  else {
    __ptr = malloc(iVar3 << 2);
    iVar5 = *(int *)(iVar4 + 0xb0);
    iVar2 = 0;
    iVar4 = 0;
    do {
      iVar4 = iVar4 + 1;
      if ((int)__ptr + iVar2 != 0) {
        *(undefined4 *)((int)__ptr + iVar2) = *(undefined4 *)(iVar5 + iVar2);
      }
      iVar2 = iVar2 + 4;
    } while (iVar4 != iVar3);
  }
  free(__ptr);
  if (iVar3 < iVar1) {
    return;
  }
  iVar3 = FUN_002bffb0(param_1,iVar1);
  if (iVar3 == 0) {
    return;
  }
  switch(iVar1 - 1U) {
  case 0:
    (**(code **)(*param_1 + 0x48))(param_1,param_3);
    break;
  case 1:
    (**(code **)(*param_1 + 0x4c))(param_1,param_3);
    break;
  case 2:
    (**(code **)(*param_1 + 0x50))(param_1,param_3);
    break;
  case 3:
    (**(code **)(*param_1 + 0x54))(param_1,param_3);
    break;
  case 4:
    (**(code **)(*param_1 + 0x58))(param_1,param_3);
    break;
  case 5:
    (**(code **)(*param_1 + 0x5c))(param_1,param_3);
    break;
  default:
    if (5 < iVar1 - 1U) {
      return;
    }
  }
  iVar1 = param_1[9];
  if (*(int *)(iVar1 + 0x60) != 0) {
    return;
  }
  if (*(int *)(iVar1 + 100) == -1) {
    return;
  }
  if (*(int **)(iVar1 + 0x6c) == (int *)0x0) {
    return;
  }
  (**(code **)(**(int **)(iVar1 + 0x6c) + 8))();
  return;
}

