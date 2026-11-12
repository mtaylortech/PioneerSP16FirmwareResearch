/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_0026b6ac(int param_1,int param_2,int param_3,undefined4 param_4)

{
  int iVar1;
  int iVar2;
  int iVar3;
  int *piVar4;
  code *pcVar5;
  int iVar6;
  undefined1 auStack_20 [4];
  undefined1 auStack_1c [4];
  
  if (*(int *)(param_1 + 0x6b0) == param_2) {
    if (param_3 == 0) {
      iVar2 = FUN_0062e318(DAT_0026b888,param_4);
      iVar1 = DAT_0026b888;
      if (iVar2 == 0) {
        iVar2 = 0;
        do {
          iVar6 = iVar2;
          if (*(int *)(param_1 + 0x6b8) + -1 <= iVar6) goto LAB_0026b7e0;
          iVar3 = FUN_0062e318(iVar1 + (iVar6 + 1) * 4,param_4);
          iVar2 = iVar6 + 1;
        } while (iVar3 == 0);
        (**(code **)(**(int **)(param_1 + 0x6ac) + 0x20))(*(int **)(param_1 + 0x6ac),iVar6);
LAB_0026b7e0:
        (**(code **)(**(int **)(param_1 + 0x6b0) + 0x3c))(*(int **)(param_1 + 0x6b0),1,1);
        piVar4 = *(int **)(param_1 + 0x6b0);
        pcVar5 = *(code **)(*piVar4 + 0x34);
        FUN_006c173c(auStack_1c,0x42,0x7d,0xa5);
        (*pcVar5)(piVar4,1,0,auStack_1c);
        FUN_006a0280(auStack_1c);
      }
      else {
        (**(code **)(**(int **)(param_1 + 0x6ac) + 0x1c))();
        (**(code **)(**(int **)(param_1 + 0x6b0) + 0x3c))(*(int **)(param_1 + 0x6b0),1,0);
        piVar4 = *(int **)(param_1 + 0x6b0);
        pcVar5 = *(code **)(*piVar4 + 0x34);
        FUN_006c1724(auStack_20,0x5a,0x61,0x6b);
        (*pcVar5)(piVar4,1,1,auStack_20);
        FUN_006a0280(auStack_20);
      }
    }
    else if (param_3 == 1) {
      iVar1 = FUN_0062e318(DAT_0026b880,param_4);
      if (iVar1 == 0) {
        iVar1 = FUN_0062e318(DAT_0026b884,param_4);
        if (iVar1 != 0) {
          (**(code **)(**(int **)(param_1 + 0x6ac) + 0x38))(*(int **)(param_1 + 0x6ac),1);
        }
      }
      else {
        (**(code **)(**(int **)(param_1 + 0x6ac) + 0x38))(*(int **)(param_1 + 0x6ac),0);
      }
    }
  }
  return;
}

