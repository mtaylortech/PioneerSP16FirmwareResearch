/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

int * FUN_007c4b70(int *param_1)

{
  int iVar1;
  int iVar2;
  int *piVar3;
  
  iVar1 = DAT_007c4d4c;
  param_1[0x1c] = DAT_007c4d4c + 0xc4;
  *param_1 = iVar1;
  do {
    iVar2 = param_1[0x26];
    iVar1 = (iVar2 + -1) * 4;
    do {
      if (iVar2 < 1) {
        if (param_1[0x25] != 0) {
          free((void *)param_1[0x24]);
          param_1[0x24] = 0;
          param_1[0x25] = 0;
        }
        param_1[0x26] = 0;
        if ((int *)param_1[0x2c] != (int *)0x0) {
          iVar1 = *(int *)param_1[0x2c];
          param_1[0x2c] = 0;
          (**(code **)(iVar1 + 4))();
          if ((int *)param_1[0x2c] != (int *)0x0) {
            (**(code **)(*(int *)param_1[0x2c] + 4))();
          }
        }
        if ((int *)param_1[0x2b] != (int *)0x0) {
          (**(code **)(*(int *)param_1[0x2b] + 4))();
        }
        do {
          iVar2 = param_1[0x26];
          iVar1 = (iVar2 + -1) * 4;
          do {
            if (iVar2 < 1) {
              free((void *)param_1[0x24]);
              FUN_00696394(param_1 + 0x1c);
              FUN_007c2764(param_1);
              return param_1;
            }
            iVar2 = iVar2 + -1;
            param_1[0x26] = iVar2;
            piVar3 = *(int **)(param_1[0x24] + iVar1);
            iVar1 = iVar1 + -4;
          } while (piVar3 == (int *)0x0);
          FUN_006a0280(piVar3 + 2);
          FUN_00627f38(piVar3 + 1);
          if ((int *)*piVar3 != (int *)0x0) {
            (**(code **)(*(int *)*piVar3 + 4))();
          }
          operator_delete(piVar3);
        } while( true );
      }
      iVar2 = iVar2 + -1;
      param_1[0x26] = iVar2;
      piVar3 = *(int **)(param_1[0x24] + iVar1);
      iVar1 = iVar1 + -4;
    } while (piVar3 == (int *)0x0);
    FUN_006a0280(piVar3 + 2);
    FUN_00627f38(piVar3 + 1);
    if ((int *)*piVar3 != (int *)0x0) {
      (**(code **)(*(int *)*piVar3 + 4))();
    }
    operator_delete(piVar3);
  } while( true );
}

