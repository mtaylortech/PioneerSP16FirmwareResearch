/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

int * candidate_007fd028(int *param_1)

{
  int *piVar1;
  int iVar2;
  int iVar3;
  
  do {
    iVar3 = param_1[2];
    iVar2 = (iVar3 + -1) * 4;
    do {
      if (iVar3 < 1) {
        free((void *)*param_1);
        return param_1;
      }
      iVar3 = iVar3 + -1;
      param_1[2] = iVar3;
      piVar1 = (int *)(*param_1 + iVar2);
      iVar2 = iVar2 + -4;
    } while ((int *)*piVar1 == (int *)0x0);
    (**(code **)(*(int *)*piVar1 + 4))();
  } while( true );
}

